"""
Module detecting unused custom errors
"""
from typing import List, Tuple

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
        defined_custom_errors: List[Tuple[CustomError,str]] = []
        custom_reverts: List[SolidityCustomRevert] = []
        unused_custom_errors: List[Tuple[CustomError,str]] = []

        # Collect all custom errors defined in the contracts
        for contract in self.compilation_unit.contracts:
            contract.custom_errors_declared
            for custom_error in contract.custom_errors:
                defined_custom_errors.append((custom_error, custom_error.contract.file_scope.filename.short))

        # Add custom errors defined outside of contracts
        for custom_error in self.compilation_unit.custom_errors:
            defined_custom_errors.append((custom_error, custom_error.file_scope.filename.short))

        # Collect all custom errors used in revertsCustomError
        for contract in self.compilation_unit.contracts:
            for function in contract.functions_and_modifiers:
                for internal_call in function.internal_calls:
                    if isinstance(internal_call, SolidityCustomRevert):
                        custom_reverts.append(internal_call)

        # Find unused custom errors
        for defined_error, file_name in defined_custom_errors:
            if not any(defined_error.name in custom_revert.name for custom_revert in custom_reverts):
                unused_custom_errors.append((defined_error, file_name))

        results = []
        if len(unused_custom_errors) > 0:
            info: DETECTOR_INFO = ["The following unused error(s) should be removed:"]
            for custom_error, file_name in unused_custom_errors:
                info += ["\n\t-", custom_error.full_name, " (", file_name, ")\n"]
            results.append(self.generate_result(info))

        return results