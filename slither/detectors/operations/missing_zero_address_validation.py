"""
Module detecting missing zero address validation

"""
from typing import List, Set
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.variable import Variable

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.variables.constant import Constant
from slither.utils.output import Output

def _collect(contract: Contract, targets: List[Variable], zero_addresses: List[Variable]) -> None:
    """
        TODO: Add description
    """

    for function in contract.functions:
        for ir in function.slithir_operations:
            if isinstance(ir, TypeConversion) and ir.type == ElementaryType("address") and ir.variable == Constant("0"):
                if ir.lvalue not in zero_addresses:
                    zero_addresses.append(ir.lvalue)

        for param in function.parameters:
            if param.type == ElementaryType("address") and param not in targets:
                targets.append(param)

        # We also need to check the modifiers
        for mod in function.modifiers:
            for param in mod.parameters:
                if param.type == ElementaryType("address") and param not in targets:
                    targets.append(param)

            for ir in mod.all_slithir_operations():
                if isinstance(ir, TypeConversion) and ir.type == ElementaryType("address") and ir.variable == Constant("0"):
                    if ir.lvalue not in zero_addresses:
                        zero_addresses.append(ir.lvalue)

def _performs_address_check(function: FunctionContract, targets: List[Variable], zero_addresses: List[Variable], removed: List[Variable]) -> bool:
    """
        TODO: Add description
    """

    performs_check: bool = False

    for ir in function.all_slithir_operations():
        # If it is a binary operation
        if isinstance(ir, Binary):
            if ir.type == BinaryType.EQUAL or ir.type == BinaryType.NOT_EQUAL:
                if ir.variable_left in targets and (ir.variable_right in zero_addresses or ir.variable_right == 0):
                    for t in targets:
                        if t != ir.variable_left and is_dependent(ir.variable_left, t, ir.function) and t not in removed:
                            removed.append(t)
                    if ir.variable_left not in removed:
                        removed.append(ir.variable_left)
                    performs_check = True

        # If an internal call or a library call was made
        elif isinstance(ir, InternalCall) or isinstance(ir, LibraryCall):
            if _performs_address_check(ir.function, targets, zero_addresses, removed):
                for t in targets:
                    if t not in removed and t in ir.arguments:
                        for r in removed:
                            if r != t and is_dependent(r, t, ir.function.contract):
                                if t not in removed:
                                    removed.append(t)
                performs_check = True
    return performs_check

class MissingZeroAddressValidation(AbstractDetector):
    """
    Missing zero address validation
    """

    ARGUMENT = "missing-zero-check"
    HELP = "Missing Zero Address Validation"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#missing-zero-address-validation"
    WIKI_TITLE = "Missing zero address validation"
    WIKI_DESCRIPTION = "Detect missing zero address validation."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {

  modifier onlyAdmin {
    if (msg.sender != owner) throw;
    _;
  }

  function updateOwner(address newOwner) onlyAdmin external {
    owner = newOwner;
  }
}
```
Bob calls `updateOwner` without specifying the `newOwner`, so Bob loses ownership of the contract.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Check that the address is not zero."

    def _detect_missing_zero_address_validation(self, contract: Contract, targets: List[Variable], zero_addresses: List[Variable], removed: List[Variable]) -> None:
        """
            TODO: Add description
        """
        if targets:
            for function in contract.functions:
                # Perform check inside the function
                _performs_address_check(function, targets, zero_addresses, removed)

    def _detect(self) -> List[Output]:
        """Detect if addresses are zero address validated before use.
        Returns:
            list: {'(function, node)'}
        """

        # Check derived contracts for missing zero address validation
        results: List[Output] = []
        targets: List[Variable] = []
        zero_addresses: List[Variable] = []
        removed: List[Variable] = []

        for contract in self.compilation_unit.contracts_derived:
            _collect(contract, targets, zero_addresses)

            self._detect_missing_zero_address_validation(contract, targets, zero_addresses, removed)

        missing_zero_address_validation = list(set(targets) - set(removed))

        for var in missing_zero_address_validation:
            info = [var, " lacks a zero check "]
            res = self.generate_result(info)
            results.append(res)

        return results
