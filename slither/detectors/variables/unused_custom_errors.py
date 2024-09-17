"""
Module detecting unused custom errors
"""
from typing import List, Dict

from slither.core.compilation_unit import SlitherCompilationUnit
from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.solidity_variables import SolidityCustomRevert
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output

class UnusedCustomErrors(AbstractDetector):
    """
    Unused custom errors detector
    """

    ARGUMENT = "unused-custom-errors"
    HELP = "Unused Custom Errors"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-custom-error"

    WIKI_TITLE = "Unused custom error"
    WIKI_DESCRIPTION = "Unused custom error."
    WIKI_EXPLOIT_SCENARIO = ""
    WIKI_RECOMMENDATION = "Remove unused custom errors."

    def _detect(self) -> List[Output]:


        """Detect unused custom errors"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            for custom_error in c.custom_errors:
                if not self._isCustomErrorUsed(custom_error):
                    info: DETECTOR_INFO = ["Unused custom error: ", custom_error.name, "\n"]
                    json = self.generate_result(info)
                    results.append(json)
        return results

    def _isCustomErrorUsed(self, custom_error: CustomError) -> bool:
        for c in self.compilation_unit.contracts_derived:
            for f in c.functions:
                for int_call in f._internal_calls:
                    print("Comparing: ", int_call.name, custom_error.name)
                    if type(int_call) is SolidityCustomRevert and custom_error.name in int_call.name:
                        return True
        return False