"""
Module detecting unused custom errors
"""
from typing import List, Set

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
        defined_custom_errors: Set[CustomError] = set()
        custom_reverts: Set[SolidityCustomRevert] = set()
        unused_custom_errors: Set[CustomError] = set()

        # Collect all custom errors defined in the contracts
        for contract in self.compilation_unit.contracts:
            for custom_error in contract.custom_errors:
                defined_custom_errors.add(custom_error)

        # Add custom errors defined outside of contracts
        for custom_error in self.compilation_unit.custom_errors:
            defined_custom_errors.add(custom_error)

        # Collect all used custom errors
        for contract in self.compilation_unit.contracts:
            for function in contract.functions_and_modifiers:
                for internal_call in function.internal_calls:
                    if isinstance(internal_call, SolidityCustomRevert):
                        custom_reverts.add(internal_call)

        # Find unused custom errors
        for defined_error in defined_custom_errors:
            if not any(defined_error.name in custom_revert.name for custom_revert in custom_reverts):
                unused_custom_errors.add(defined_error)

        results = []
        for custom_error in unused_custom_errors:
            info: DETECTOR_INFO = ["Unused custom error: # ", custom_error.full_name, "\n"]
            json = self.generate_result(info)
            results.append(json)

        return results