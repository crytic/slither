"""
Module detecting unused custom errors
"""
from typing import List, Dict

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.formatters.variables.unused_state_variables import custom_format
from slither.utils.output import Output

class UnusedCustomErrors(AbstractDetector):
    """
    Unused custom errors detector
    """

    ARGUMENT = "unused-custom-errors"
    HELP = "Unused Custom Errors"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-state-variable"

    WIKI_TITLE = "Unused state variable"
    WIKI_DESCRIPTION = "Unused state variable."
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = "Remove unused state variables."

    def _detect(self) -> List[Output]:
        """Detect unused state variables"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            for custom_error in c.custom_errors:
                info: DETECTOR_INFO = [custom_error.name, " is never used in ", c, "\n"]
                json = self.generate_result(info)
                results.append(json)

        return results

    @staticmethod
    def _format(compilation_unit: SlitherCompilationUnit, result: Dict) -> None:
        custom_format(compilation_unit, result)
