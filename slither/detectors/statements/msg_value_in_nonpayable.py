from typing import List, Tuple
from slither.utils.output import Output

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.declarations.function import Function


class MsgValueInNonPayable(AbstractDetector):
    """
    Detects uses of msg.value in functions that cannot be reached
    from any payable public/external entry point.

    Such msg.value usages are provably meaningless:
    - msg.value will always be 0, or
    - execution will always revert
    """

    ARGUMENT = "msg-value-in-nonpayable"
    HELP = "msg.value used in functions unreachable from payable entry points"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/issues/2781"
    WIKI_TITLE = "msg.value used in functions unreachable from payable entry points"

    WIKI_DESCRIPTION = """
    Detects functions that directly read `msg.value` but cannot be reached
    from any payable public or external entry point. In such cases,
    `msg.value` is provably meaningless (always zero or execution always reverts).
    """

    WIKI_EXPLOIT_SCENARIO = """
    This issue is not directly exploitable. However, relying on `msg.value` in
    functions that are unreachable from payable entry points indicates
    incorrect assumptions about ETH flow and may result in dead or misleading code.

    For example:
    ```solidity
    contract Subscription {
        mapping(address => bool) public subscribed;

        // Developer expects users to pay here
        function subscribe() external {
            require(msg.value >= 1 ether, "Subscription fee required");
            subscribed[msg.sender] = true;
        }
    }
    ```
    Here, `subscribe()` is not payable, so it can never receive ETH.
    As a result, `msg.value` is always zero and the `require` statement will always fail, making the function unusable.
    """

    WIKI_RECOMMENDATION = """
    Make the function payable if it is intended to receive ETH, or remove
    the `msg.value`-based logic if ETH should never be sent to this code path.
    """

    def _detect(self) -> List[Output]:
        results = []

        # Detect direct msg.value usage only
        for contract in self.contracts:
            for func in contract.functions:

                # Skip interfaces / abstract / unimplemented functions
                if not func.is_implemented:
                    continue

                # Skip functions that do not directly use msg.value
                # (either in the function body or in attached modifiers)
                if not self._uses_msg_value(func) and not any(
                    self._uses_msg_value(i) for i in func.modifiers
                ):
                    continue

                # payable functions are always valid entry points for msg.value
                if func.payable:
                    continue

                # Collect public/external callers and classify them
                payable_callers, non_payable_callers = self._get_entry_point_callers(func)

                # If at least one payable entry point can reach this function,
                # msg.value usage is valid
                if payable_callers:
                    continue

                # Otherwise Flag, msg.value is unreachable from payable contexts
                info = self._build_info(func, non_payable_callers)
                results.append(self.generate_result(info))

        return results

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _uses_msg_value(self, function) -> bool:
        """
        Returns True if the function directly reads msg.value
        """
        for node in function.nodes:
            for ir in node.irs:
                for read in ir.read:
                    if isinstance(read, SolidityVariableComposed) and read.name == "msg.value":
                        return True
        return False

    def _get_entry_point_callers(self, function: Function) -> Tuple[List[Function], List[Function]]:
        """
        Walk the reverse call graph using Slither's
        `all_reachable_from_functions`.

        Returns:
            (payable_callers, non_payable_callers)

        Only public/external functions are considered entry points.
        """
        payable_callers = []
        non_payable_callers = []

        if function.visibility in ("public", "external"):
            if function.payable:
                payable_callers.append(function)
            else:
                non_payable_callers.append(function)

        for func in function.all_reachable_from_functions:
            if isinstance(func, Function) and func.visibility in ["public", "external"]:
                if func.payable:
                    payable_callers.append(func)
                else:
                    non_payable_callers.append(func)
        return (payable_callers, non_payable_callers)

    def _build_info(self, func: Function, non_payable_callers: list) -> DETECTOR_INFO:
        info: DETECTOR_INFO = [
            func,
            " uses msg.value but is not reachable from any payable function\n",
        ]

        filtered_non_payable_callers = [c for c in non_payable_callers if c != func]

        if filtered_non_payable_callers:
            info.append("\tNon-payable entry points that can reach this function:\n")
            for caller in filtered_non_payable_callers:
                info.extend(["\t- ", caller, "\n"])

        return info
