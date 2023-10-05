from typing import List, Optional

from slither.core.declarations import SolidityFunction, Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import SolidityCall
from slither.utils.output import Output


def _assembly_node(function: Function) -> Optional[SolidityCall]:
    """
    Check if there is a node that use return in assembly

    Args:
        function:

    Returns:

    """

    for ir in function.all_slithir_operations():
        if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
            "return(uint256,uint256)"
        ):
            return ir
    return None


class IncorrectReturn(AbstractDetector):
    """
    Check for cases where a return(a,b) is used in an assembly function
    """

    ARGUMENT = "incorrect-return"
    HELP = "If a `return` is incorrectly used in assembly mode."
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-assembly-return"

    WIKI_TITLE = "Incorrect return in assembly"
    WIKI_DESCRIPTION = "Detect if `return` in an assembly block halts unexpectedly the execution."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {
    function f() internal returns (uint a, uint b) {
        assembly {
            return (5, 6)
        }
    }

    function g() returns (bool){
        f();
        return true;
    }
}
```
The return statement in `f` will cause execution in `g` to halt.
The function will return 6 bytes starting from offset 5, instead of returning a boolean."""

    WIKI_RECOMMENDATION = "Use the `leave` statement."

    # pylint: disable=too-many-nested-blocks
    def _detect(self) -> List[Output]:
        results: List[Output] = []
        for c in self.contracts:
            for f in c.functions_and_modifiers_declared:

                for node in f.nodes:
                    if node.sons:
                        for function_called in node.internal_calls:
                            if isinstance(function_called, Function):
                                found = _assembly_node(function_called)
                                if found:

                                    info: DETECTOR_INFO = [
                                        f,
                                        " calls ",
                                        function_called,
                                        " which halt the execution ",
                                        found.node,
                                        "\n",
                                    ]
                                    json = self.generate_result(info)

                                    results.append(json)

        return results
