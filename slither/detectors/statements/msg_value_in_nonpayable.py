"""
Detector for msg.value usage in functions unreachable from payable entry points.
Related to issue #2781.
"""

from __future__ import annotations

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

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#msgvalue-in-nonpayable"
    WIKI_TITLE = "msg.value in non-payable function"

    WIKI_DESCRIPTION = """
Detects functions that read `msg.value` but cannot be reached from any payable
public or external entry point. In such cases, `msg.value` is always zero or
execution always reverts."""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Subscription {
    mapping(address => bool) public subscribed;

    function subscribe() external {
        require(msg.value >= 1 ether, "Fee required");
        subscribed[msg.sender] = true;
    }
}
```
`subscribe()` is not payable, so it cannot receive ETH. `msg.value` is always zero
and the require always fails, making the function unusable."""

    WIKI_RECOMMENDATION = """
Either mark the function as `payable` if it should receive ETH, or remove the
`msg.value` check since it will always be zero in non-payable contexts."""

    # Only applicable to Solidity (Vyper handles payable differently)
    LANGUAGE = "solidity"

    def _detect(self) -> list[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            for func in contract.functions:
                # Skip if not implemented
                if not func.is_implemented:
                    continue

                # Check if function or its modifiers use msg.value
                if not self._uses_msg_value(func) and not any(
                    self._uses_msg_value(m) for m in func.modifiers
                ):
                    continue

                # Payable functions are valid entry points for msg.value
                if func.payable:
                    continue

                # Get all entry points that can reach this function
                payable_callers, non_payable_callers = self._get_entry_point_callers(func)

                # If any payable entry point reaches this function, msg.value is valid
                if payable_callers:
                    continue

                # Otherwise, msg.value is unreachable from payable contexts - flag it
                info: DETECTOR_INFO = self._build_info(func, non_payable_callers)
                results.append(self.generate_result(info))

        return results

    def _uses_msg_value(self, function: Function) -> bool:
        """Returns True if the function directly reads msg.value."""
        for node in function.nodes:
            for ir in node.irs:
                for read in ir.read:
                    if isinstance(read, SolidityVariableComposed) and read.name == "msg.value":
                        return True
        return False

    def _get_entry_point_callers(self, function: Function) -> tuple[list[Function], list[Function]]:
        """
        Walk the reverse call graph to find all public/external entry points.

        Returns:
            (payable_callers, non_payable_callers) - only public/external functions
        """
        payable_callers = []
        non_payable_callers = []

        # Include the function itself if it's an entry point
        if function.visibility in ("public", "external"):
            if function.payable:
                payable_callers.append(function)
            else:
                non_payable_callers.append(function)

        # Check all functions that can reach this one
        for caller in function.all_reachable_from_functions:
            if not isinstance(caller, Function):
                continue
            if caller.visibility not in ("public", "external"):
                continue

            if caller.payable:
                payable_callers.append(caller)
            else:
                non_payable_callers.append(caller)

        return payable_callers, non_payable_callers

    def _build_info(self, func: Function, non_payable_callers: list[Function]) -> DETECTOR_INFO:
        """Build properly formatted detector output using Slither objects."""
        info: DETECTOR_INFO = [
            func,
            " uses msg.value but is not reachable from any payable function\n",
        ]

        if non_payable_callers:
            info.append("\tNon-payable entry points that can reach this function:\n")
            for caller in non_payable_callers:
                if caller != func:
                    info.extend(["\t- ", caller, "\n"])

        return info
