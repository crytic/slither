"""
Module detecting state changes in assert calls
"""
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations.internal_call import InternalCall


def detect_assert_state_change(contract):
    """
    Detects and returns all nodes with assert calls that change contract state from within the invariant
    :param contract: Contract to detect
    :return: A list of nodes with assert calls that change contract state from within the invariant
    """

    # Create our result set.
    # List of tuples (function, node)
    results = []

    # Loop for each function and modifier.
    for function in contract.functions_declared + contract.modifiers_declared:
        for node in function.nodes:
            # Detect assert() calls
            if any(c.name == "assert(bool)" for c in node.internal_calls) and (
                # Detect direct changes to state
                node.state_variables_written
                or
                # Detect changes to state via function calls
                any(
                    ir
                    for ir in node.irs
                    if isinstance(ir, InternalCall) and ir.function.state_variables_written
                )
            ):
                results.append((function, node))

    # Return the resulting set of nodes
    return results


class AssertStateChange(AbstractDetector):
    """
    Assert state change
    """

    ARGUMENT = "assert-state-change"
    HELP = "Assert state change"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#assert-state-change"
    WIKI_TITLE = "Assert state change"
    WIKI_DESCRIPTION = """Incorrect use of `assert()`. See Solidity best [practices](https://solidity.readthedocs.io/en/latest/control-structures.html#id4)."""

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {

  uint s_a;

  function bad() public {
    assert((s_a += 1) > 10);
  }
}
```
The assert in `bad()` increments the state variable `s_a` while checking for the condition.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """Use `require` for invariants modifying the state."""

    def _detect(self):
        """
        Detect assert calls that change state from within the invariant
        """
        results = []
        for contract in self.contracts:
            assert_state_change = detect_assert_state_change(contract)
            for (func, node) in assert_state_change:
                info = [func, " has an assert() call which possibly changes state.\n"]
                info += ["\t-", node, "\n"]
                info += [
                    "Consider using require() or change the invariant to not modify the state.\n"
                ]
                res = self.generate_result(info)
                results.append(res)
        return results
