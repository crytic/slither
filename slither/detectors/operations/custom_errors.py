from packaging.version import Version

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import SolidityCall
from slither.slithir.variables import Constant
from slither.utils.output import Output


class GasCustomErrors(AbstractDetector):
    ARGUMENT = "custom-errors"
    HELP = "Literal revert strings that could use custom errors"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH
    LANGUAGE = "solidity"
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#custom-errors"
    WIKI_TITLE = "Custom errors"
    WIKI_DESCRIPTION = (
        "Finds nonempty literal strings passed to require or revert on Solidity >=0.8.4. "
        "Named custom errors can reduce deployment and revert-data overhead. Dynamic messages, "
        "bare reverts and existing custom errors are excluded."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
function check(bool ok) external pure { require(ok, "denied"); }
// Consider: if (!ok) revert Denied();
```
"""
    WIKI_RECOMMENDATION = (
        "Consider a named custom error, using if (!condition) revert NamedError() where needed. "
        "Review changed error selectors, ABI expectations and revert tests before replacing strings."
    )

    def _detect(self) -> list[Output]:
        if Version(self.compilation_unit.solc_version) < Version("0.8.4"):
            return []
        results = []
        for function in self.compilation_unit.functions_and_modifiers:
            for node in function.nodes:
                for ir in node.irs:
                    if not isinstance(ir, SolidityCall):
                        continue
                    if ir.function.full_name not in ("require(bool,string)", "revert(string)"):
                        continue
                    message = ir.arguments[-1]
                    if not isinstance(message, Constant) or not message.value:
                        continue
                    results.append(
                        self.generate_result(
                            [
                                function,
                                " uses a literal revert string in ",
                                node,
                                "; consider a named custom error (changes the error ABI).\n",
                            ]
                        )
                    )
        return sorted(results, key=lambda r: r.data["description"])
