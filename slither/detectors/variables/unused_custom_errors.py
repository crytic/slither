"""
Module detecting unused custom errors
"""

from slither.core.declarations import Function, Contract
from slither.core.declarations.custom_error import CustomError
from slither.core.declarations.custom_error_contract import CustomErrorContract
from slither.core.declarations.custom_error_top_level import CustomErrorTopLevel
from slither.core.declarations.solidity_variables import SolidityCustomRevert
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import SolidityCall
from slither.utils.output import Output


def _detect_unused_custom_errors_in_contract(
    contract: Contract,
) -> list[CustomErrorContract]:
    """
    Detect unused custom errors declared in a contract.

    Args:
        contract: The contract to analyze

    Returns:
        List of unused custom errors declared in the contract
    """
    # Get all custom errors declared in this contract
    declared_errors = set(contract.custom_errors_declared)

    if not declared_errors:
        return []

    # Find all custom errors used in this contract and its derived contracts
    used_errors: set[CustomError] = set()

    # Check all functions in the contract (including inherited)
    all_functions = [
        f
        for f in contract.all_functions_called + list(contract.modifiers)
        if isinstance(f, Function)
    ]

    for func in all_functions:
        for node in func.nodes:
            for ir in node.all_slithir_operations():
                if isinstance(ir, SolidityCall) and isinstance(
                    ir.function, SolidityCustomRevert
                ):
                    used_errors.add(ir.function.custom_error)

    # Return unused errors
    return [error for error in declared_errors if error not in used_errors]


def _detect_unused_custom_errors_top_level(
    compilation_unit,
) -> list[CustomErrorTopLevel]:
    """
    Detect unused top-level custom errors.

    Args:
        compilation_unit: The compilation unit to analyze

    Returns:
        List of unused top-level custom errors
    """
    # Get all top-level custom errors
    top_level_errors = set(compilation_unit.custom_errors)

    if not top_level_errors:
        return []

    # Find all custom errors used across all contracts
    used_errors: set[CustomError] = set()

    for contract in compilation_unit.contracts:
        all_functions = [
            f
            for f in contract.all_functions_called + list(contract.modifiers)
            if isinstance(f, Function)
        ]

        for func in all_functions:
            for node in func.nodes:
                for ir in node.all_slithir_operations():
                    if isinstance(ir, SolidityCall) and isinstance(
                        ir.function, SolidityCustomRevert
                    ):
                        used_errors.add(ir.function.custom_error)

    # Also check top-level functions
    for func in compilation_unit.functions_top_level:
        for node in func.nodes:
            for ir in node.all_slithir_operations():
                if isinstance(ir, SolidityCall) and isinstance(
                    ir.function, SolidityCustomRevert
                ):
                    used_errors.add(ir.function.custom_error)

    # Return unused top-level errors
    return [error for error in top_level_errors if error not in used_errors]


class UnusedCustomErrors(AbstractDetector):
    """
    Detector for unused custom error definitions
    """

    ARGUMENT = "unused-error"
    HELP = "Unused custom error definitions"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-custom-error"

    WIKI_TITLE = "Unused custom error"
    WIKI_DESCRIPTION = "Detects custom error definitions that are never used. Unused custom errors may indicate missing error handling logic or dead code that should be removed."

    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract VendingMachine {
    error Unauthorized();  // Defined but never used
    address payable owner = payable(msg.sender);

    function withdraw() public {
        // Missing: if (msg.sender != owner) revert Unauthorized();
        owner.transfer(address(this).balance);
    }
}
```
The `Unauthorized` error is defined but never used, suggesting the developer may have forgotten to add access control checks."""

    WIKI_RECOMMENDATION = "Use the custom error in a `revert` statement, or remove the error definition if it is not needed."

    def _detect(self) -> list[Output]:
        """Detect unused custom errors"""
        results: list[Output] = []

        # Check for unused custom errors in each contract
        for contract in self.compilation_unit.contracts_derived:
            if contract.is_signature_only():
                continue

            unused_errors = _detect_unused_custom_errors_in_contract(contract)
            for error in unused_errors:
                info: DETECTOR_INFO = [
                    error,
                    " is declared but never used in ",
                    contract,
                    "\n",
                ]
                results.append(self.generate_result(info))

        # Check for unused top-level custom errors
        unused_top_level = _detect_unused_custom_errors_top_level(self.compilation_unit)
        for error in unused_top_level:
            info = [error, " is declared but never used\n"]
            results.append(self.generate_result(info))

        return results
