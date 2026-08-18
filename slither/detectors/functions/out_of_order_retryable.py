from slither.core.cfg.node import Node
from slither.core.declarations import Function, FunctionContract
from slither.slithir.operations import HighLevelCall
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


class OutOfOrderRetryable(AbstractDetector):
    ARGUMENT = "out-of-order-retryable"
    HELP = "Out-of-order retryable transactions"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#out-of-order-retryable-transactions"

    WIKI_TITLE = "Out-of-order retryable transactions"
    WIKI_DESCRIPTION = "Out-of-order retryable transactions"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract L1 {
    function doStuffOnL2() external {
        // Retryable A
        IInbox(inbox).createRetryableTicket({
            to: l2contract,
            l2CallValue: 0,
            maxSubmissionCost: maxSubmissionCost,
            excessFeeRefundAddress: msg.sender,
            callValueRefundAddress: msg.sender,
            gasLimit: gasLimit,
            maxFeePerGas: maxFeePerGas,
            data: abi.encodeCall(l2contract.claim_rewards, ())
        });
        // Retryable B
        IInbox(inbox).createRetryableTicket({
            to: l2contract,
            l2CallValue: 0,
            maxSubmissionCost: maxSubmissionCost,
            excessFeeRefundAddress: msg.sender,
            callValueRefundAddress: msg.sender,
            gasLimit: gas,
            maxFeePerGas: maxFeePerGas,
            data: abi.encodeCall(l2contract.unstake, ())
        });
    }
}

contract L2 {
    function claim_rewards() public {
        // rewards is computed based on balance and staking period
        uint unclaimed_rewards = _compute_and_update_rewards();
        token.safeTransfer(msg.sender, unclaimed_rewards);
    }

    // Call claim_rewards before unstaking, otherwise you lose your rewards
    function unstake() public {
        _free_rewards(); // clean up rewards related variables
        balance = balance[msg.sender];
        balance[msg.sender] = 0;
        staked_token.safeTransfer(msg.sender, balance);
    }
}
```
Bob calls `doStuffOnL2` but the first retryable ticket calling `claim_rewards` fails. The second retryable ticket calling `unstake` is executed successfully. As a result, Bob loses his rewards."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Do not rely on the order or successful execution of retryable tickets."

    key = "OUTOFORDERRETRYABLE"

    def _detect_multiple_tickets(
        self, function: FunctionContract, node: Node, visited: list[Node]
    ) -> None:
        if node in visited:
            return

        visited = visited + [node]

        fathers_context = []

        for father in node.fathers:
            if self.key in father.context:
                fathers_context += father.context[self.key]

        # Exclude path that dont bring further information
        if node in self.visited_all_paths:
            if all(f_c in self.visited_all_paths[node] for f_c in fathers_context):
                return
        else:
            self.visited_all_paths[node] = []

        self.visited_all_paths[node] = self.visited_all_paths[node] + fathers_context

        if self.key not in node.context:
            node.context[self.key] = fathers_context

        # include ops from internal function calls
        internal_ops = []
        for ir in node.internal_calls:
            if isinstance(ir.function, Function):
                internal_ops += ir.function.all_slithir_operations()

        # analyze node for retryable tickets
        for ir in node.irs + internal_ops:
            if (
                isinstance(ir, HighLevelCall)
                and isinstance(ir.function, Function)
                and ir.function.name
                in [
                    "createRetryableTicket",
                    "outboundTransferCustomRefund",
                    "unsafeCreateRetryableTicket",
                ]
            ):
                node.context[self.key].append(node)

        if len(node.context[self.key]) > 1:
            self.results.append(node.context[self.key])
            return

        for son in node.sons:
            self._detect_multiple_tickets(function, son, visited)

    def _detect(self) -> list[Output]:
        results = []

        self.results = []
        self.visited_all_paths = {}

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                if (
                    function.is_implemented
                    and function.contract_declarer == contract
                    and function.entry_point
                ):
                    function.entry_point.context[self.key] = []
                    self._detect_multiple_tickets(function, function.entry_point, [])

        for multiple_tickets in self.results:
            info = ["Multiple retryable tickets created in the same function:\n"]

            for x in multiple_tickets:
                info += ["\t -", x, "\n"]

            json = self.generate_result(info)
            results.append(json)

        return results
