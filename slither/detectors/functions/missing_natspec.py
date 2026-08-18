"""
Module detecting public and external functions without natspec documentation
"""

from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class MissingNatspec(AbstractDetector):
    """
    Detect public and external functions that are missing natspec documentation
    """

    ARGUMENT = "missing-natspec"
    HELP = "Public and external functions without natspec documentation"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#missing-natspec"

    WIKI_TITLE = "Missing natspec"
    WIKI_DESCRIPTION = (
        "Public and external functions make up a contract's interface, so leaving them "
        "undocumented hides intent from integrators and reviewers."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
    function withdraw(uint256 amount) external {
        // no natspec describing what amount means or who can call this
    }
}
```
A caller has no documented description of `withdraw`, making the intended behavior easy to misread."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Add natspec documentation to public and external functions."

    @staticmethod
    def _is_candidate(function: FunctionContract) -> bool:
        if function.visibility not in ("public", "external"):
            return False
        if function.is_constructor or function.is_constructor_variables:
            return False
        if function.is_fallback or function.is_receive:
            return False
        return True

    def _detect_missing_natspec(self, contract: Contract) -> list[FunctionContract]:
        ret = []
        for f in contract.functions_declared:
            if f.source_mapping.is_dependency:
                continue
            if self._is_candidate(f) and not f.has_documentation:
                ret.append(f)
        return ret

    def _detect(self) -> list[Output]:
        results = []
        for c in self.compilation_unit.contracts_derived:
            for func in self._detect_missing_natspec(c):
                info: DETECTOR_INFO = [func, " is missing natspec documentation\n"]
                res = self.generate_result(info)
                results.append(res)
        return results
