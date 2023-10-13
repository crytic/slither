from typing import List

from slither.core.declarations import SolidityFunction, Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import SolidityCall
from slither.utils.output import Output


class ReturnInsteadOfLeave(AbstractDetector):
    """
    Check for cases where a return(a,b) is used in an assembly function that also returns two variables
    """

    ARGUMENT = "return-leave"
    HELP = "If a `return` is used instead of a `leave`."
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-assembly-return"

    WIKI_TITLE = "Return instead of leave in assembly"
    WIKI_DESCRIPTION = "Detect if a `return` is used where a `leave` should be used."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {
    function f() internal returns (uint a, uint b) {
        assembly {
            return (5, 6)
        }
    }

}
```
The function will halt the execution, instead of returning a two uint."""

    WIKI_RECOMMENDATION = "Use the `leave` statement."

    def _check_function(self, f: Function) -> List[Output]:
        results: List[Output] = []

        for node in f.nodes:
            for ir in node.irs:
                if isinstance(ir, SolidityCall) and ir.function == SolidityFunction(
                    "return(uint256,uint256)"
                ):
                    info: DETECTOR_INFO = [f, " contains an incorrect call to return: ", node, "\n"]
                    json = self.generate_result(info)

                    results.append(json)
        return results

    def _detect(self) -> List[Output]:
        results: List[Output] = []
        for c in self.contracts:
            for f in c.functions_declared:

                if (
                    len(f.returns) == 2
                    and f.contains_assembly
                    and f.visibility not in ["public", "external"]
                ):
                    results += self._check_function(f)

        return results
