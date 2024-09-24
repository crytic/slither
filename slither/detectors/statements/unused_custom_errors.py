"""
Module detecting unused custom errors
"""
from typing import List
from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
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
    HELP = "Detects unused custom errors"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-custom-errors"

    WIKI_TITLE = "Unused Custom Errors"
    WIKI_DESCRIPTION = "Declaring a custom error, but never using it might indicate a mistake."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
    contract A {
        error ZeroAddressNotAllowed();
        
        address public owner;
        
        constructor(address _owner) {
            owner = _owner;
        }
    }
    ```
    Custom error `ZeroAddressNotAllowed` is declared but never used. It shall be either invoked where needed, or removed if there's no need for it.
    """
    # endregion wiki_exploit_scenario = ""
    WIKI_RECOMMENDATION = "Remove the unused custom errors."

    def _detect(self) -> List[Output]:
        """Detect unused custom errors"""
        declared_custom_errors: List[CustomError] = []
        custom_reverts: List[SolidityCustomRevert] = []
        unused_custom_errors: List[CustomError] = []

        # Collect all custom errors defined in the contracts
        for contract in self.compilation_unit.contracts:
            contract.custom_errors_declared
            for custom_error in contract.custom_errors:
                declared_custom_errors.append(custom_error)

        # Add custom errors defined outside of contracts
        for custom_error in self.compilation_unit.custom_errors:
            declared_custom_errors.append(custom_error)

        # Collect all custom errors invoked in revert statements
        for contract in self.compilation_unit.contracts:
            for function in contract.functions_and_modifiers:
                for internal_call in function.internal_calls:
                    if isinstance(internal_call, SolidityCustomRevert):
                        custom_reverts.append(internal_call)

        # Find unused custom errors
        for declared_error in declared_custom_errors:
            if not any(
                declared_error.name in custom_revert.name for custom_revert in custom_reverts
            ):
                unused_custom_errors.append(declared_error)

        results = []
        if len(unused_custom_errors) > 0:
            info: DETECTOR_INFO = ["The following unused error(s) should be removed:"]
            for custom_error in unused_custom_errors:
                file_scope = (
                    custom_error.file_scope
                    if isinstance(custom_error, CustomErrorTopLevel)
                    else custom_error.contract.file_scope
                )
                info += ["\n\t-", custom_error.full_name, " (", file_scope.filename.short, ")\n"]
            results.append(self.generate_result(info))

        return results
