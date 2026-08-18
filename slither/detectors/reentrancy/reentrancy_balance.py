"""
Re-entrancy detection

Based on heuristics, it may lead to FP and FN
Iterate over all the nodes of the graph until reaching a fixpoint
"""

from collections import namedtuple, defaultdict

from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.reentrancy.reentrancy import Reentrancy
from slither.utils.output import Output
from slither.slithir.operations import Binary, SolidityCall, HighLevelCall
from slither.core.declarations.function import Function
from slither.core.cfg.node import Node
from slither.analyses.data_dependency.data_dependency import is_dependent

# function: the vulnerable function
# call_node: the external call allowing reentrancy (may be internal function containing external call)
# external_calls: tuple of actual external call nodes (when call_node is internal function)
# balance_node: where balanceOf was called (before the external call)
FindingKey = namedtuple("FindingKey", ["function", "call_node", "external_calls", "balance_node"])
# variable: the variable in the guard that depends on stale balanceOf
# guard_node: the guard node using the stale value (after the external call)
FindingValue = namedtuple("FindingValue", ["variable", "guard_node"])


class ReentrancyBalance(Reentrancy):
    ARGUMENT = "reentrancy-balance"
    HELP = "Reentrancy vulnerabilities leading to outdated balance checks"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities"
    )

    WIKI_TITLE = "Reentrancy vulnerabilities"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detects reentrancy vulnerabilities where a balance is saved (e.g., `balanceOf`) before an external call,
and the same balance is checked again after the call. An attacker could manipulate the balance during the reentrant call,
causing the post-call check to use an outdated value."""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
interface IERC20 {
   function balanceOf(address account) external view returns (uint256);
}

interface I {
  function pay(uint256 amount) external;
}

function mint(IERC20 tk) public {
    uint amount_to_pay = 100;
    uint balance_before = tk.balanceOf(address(this));
    I(msg.sender).pay(amount_to_pay);
    require(tk.balanceOf(address(this)) - balance_before >= amount_to_pay);
    // Mint liquidity
}
```

The `balanceBefore` variable could be outdated if the external call reenter the `mint` function N times, allowing to pay the funds only once."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """Use `transferFrom` to transfer funds of a standard ERC20 token, or use reentrancy guards to prevent reentering the function."""

    STANDARD_JSON = False

    def _is_guard_node(self, node: Node) -> bool:
        """Check if node is a guard (require/assert or IF leading to revert)."""
        # Direct require/assert
        if node.contains_require_or_assert():
            return True

        # IF node - check if any immediate son is a revert
        if node.contains_if():
            for son in node.sons:
                # Check for revert() call in the son node
                for ir in son.irs:
                    if isinstance(ir, SolidityCall) and ir.function.name.startswith("revert"):
                        return True

        return False

    def find_reentrancies(self) -> defaultdict[FindingKey, set[FindingValue]]:
        result: defaultdict[FindingKey, set[FindingValue]] = defaultdict(set)
        for contract in self.contracts:
            for f in contract.functions_and_modifiers_declared:
                for node in f.nodes:
                    # Skip if no context or not a guard node
                    if self.KEY not in node.context:
                        continue
                    if not node.context[self.KEY].high_level_custom_calls_prior_calls:
                        continue
                    if not self._is_guard_node(node):
                        continue

                    # Check for external calls that could allow reentrancy
                    for call_node, external_call_nodes in node.context[self.KEY].calls.items():
                        prior_calls = node.context[
                            self.KEY
                        ].high_level_custom_calls_prior_calls.get(call_node, set())
                        for prior_ir in prior_calls:
                            found = False
                            for ir in node.irs:
                                if found:
                                    break
                                if isinstance(ir, Binary):
                                    for v in ir.read:
                                        if is_dependent(v, prior_ir.lvalue, node):
                                            # Sort external calls by node_id for deterministic output
                                            sorted_ext_calls = tuple(
                                                sorted(external_call_nodes, key=lambda x: x.node_id)
                                            )
                                            finding_key = FindingKey(
                                                function=f,
                                                call_node=call_node,
                                                external_calls=sorted_ext_calls,
                                                balance_node=prior_ir.node,
                                            )
                                            finding_value = FindingValue(
                                                variable=v,
                                                guard_node=node,
                                            )
                                            result[finding_key].add(finding_value)
                                            found = True
                                            break
                                    if found:
                                        break
        return result

    @staticmethod
    def custom_read_high_level_call(ir: HighLevelCall) -> bool:
        if isinstance(ir.function, Function) and ir.function.full_name == "balanceOf(address)":
            return True

        return False

    def _detect(self) -> list[Output]:
        super()._detect()
        reentrancies = self.find_reentrancies()

        results = []

        result_sorted = sorted(
            reentrancies.items(),
            key=lambda x: (x[0].function.name, x[0].call_node.node_id),
        )
        for (func, call_node, external_calls, balance_node), findings in result_sorted:
            findings = sorted(findings, key=lambda x: (x.variable.name, x.guard_node.node_id))

            info: list = ["Reentrancy in ", func, ":\n"]

            info += ["\tExternal call allowing reentrancy:\n"]
            info += ["\t- ", call_node, "\n"]
            # Show actual external calls if different from the call_node
            for ext_call in external_calls:
                if ext_call != call_node:
                    info += ["\t\t- ", ext_call, "\n"]

            info += ["\tBalance read before the call:\n"]
            info += ["\t- ", balance_node, "\n"]

            info += ["\tPossible stale balance used after the call in a condition:\n"]
            for finding in findings:
                info += ["\t- ", finding.guard_node, "\n"]
                info += ["\t\t- stale variable `", finding.variable.name, "`\n"]

            # Create our JSON result
            res = self.generate_result(info)

            # Add the function with the re-entrancy first
            res.add(func)

            # Add the external call
            res.add(call_node, {"underlying_type": "external_call"})
            # Add actual external calls if different from call_node
            for ext_call in external_calls:
                if ext_call != call_node:
                    res.add(ext_call, {"underlying_type": "external_call_actual"})

            # Add the balance read node (taint source)
            res.add(balance_node, {"underlying_type": "balance_before_call"})

            # Add guard nodes using stale balance
            for finding in findings:
                res.add(
                    finding.guard_node,
                    {
                        "underlying_type": "stale_balance_use",
                        "variable_name": finding.variable.name,
                    },
                )

            results.append(res)

        return results
