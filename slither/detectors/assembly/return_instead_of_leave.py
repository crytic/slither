from slither.core.declarations import SolidityFunction, Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class ReturnInsteadOfLeave(AbstractDetector):
    """
    Check for cases where a return(a,b) is used in an assembly function that also returns two variables
    """

    ARGUMENT = "return-leave"
    HELP = "If a `return` is used instead of a `leave`."
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#return-instead-of-leave-in-assembly"

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

    def _check_function(self, f: Function) -> list[Output]:
        results: list[Output] = []

        for ir in f.solidity_calls:
            if ir.function == SolidityFunction("return(uint256,uint256)"):
                info: DETECTOR_INFO = [f, " contains an incorrect call to return: ", ir.node, "\n"]
                json = self.generate_result(info)

                results.append(json)
        return results

    def _detect(self) -> list[Output]:
        results: list[Output] = []
        for c in self.contracts:
            for f in c.functions_declared:
                if (
                    len(f.returns) == 2
                    and f.contains_assembly
                    and f.visibility not in ["public", "external"]
                ):
                    results += self._check_function(f)

        return results
