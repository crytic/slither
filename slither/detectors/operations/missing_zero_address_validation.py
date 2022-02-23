"""
Module detecting missing zero address validation

"""
from typing import List, Optional, Dict

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Operation
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.variables.constant import Constant
from slither.utils.output import Output


def _get_zero_addresses(function: Function) -> List[Variable]:
    """
    Look for all the zero address (0, or address(0))

    Args:
        function (Function):

    Returns:
        List[Variable]: list of zero addresses
    """
    zero_addresses: List[Variable] = [Constant("0")]

    for ir in function.all_slithir_operations():
        if (
            isinstance(ir, TypeConversion)
            and ir.type == ElementaryType("address")
            and ir.variable == Constant("0")
        ):
            zero_addresses.append(ir.lvalue)
    return zero_addresses


def _is_checked(
    ir: Operation, targets: List[Variable], zero_addresses: List[Variable]
) -> Optional[Variable]:
    """
    Check if the IR is
        lvalue = left == right, or lvalue = left != right
    Where left is dependent on one of the target, and right is one of the zero addresses

    Args:
        ir (Operation): Ir to check
        targets (List[Variable]): list of targets
        zero_addresses (List[Variable]): list of zero address

    Returns:
        Optional[Variable
    """
    if isinstance(ir, Binary) and ir.type in [BinaryType.EQUAL, BinaryType.NOT_EQUAL]:
        for target in targets:
            if is_dependent(ir.variable_left, target, ir.function) and (
                ir.variable_right in zero_addresses
            ):
                return target
    return None


def _targets_checked_directly(function: Function, targets: List[Variable]) -> List[Variable]:
    """
    Return the list of targets checked directly

    Args:
        function (Function): function to check
        targets (List[Variable]): list of targets

    Returns:
        List[Variable]: list of targets checked
    """
    zero_addresses = _get_zero_addresses(function)
    vars_removed: List[Variable] = []

    for ir in function.all_slithir_operations():
        to_be_removed = _is_checked(ir, targets, zero_addresses)
        if to_be_removed:
            vars_removed.append(to_be_removed)

    return vars_removed


def _targets_checked_in_lib(function: Function, targets: List[Variable]) -> List[Variable]:
    """
    Return the list of targets checked in libraries.
    We need a specific handling for libraries, as the data dependencies do not work on libraries
    out of the box, as libraries can be external calls, and might not hold the actual logic based on
    the system's deployment

    Args:
        function (Function): function to check
        targets (List[Variable]): list of targets

    Returns:
        List[Variable]: list of targets checked

    """
    vars_removed: List[Variable] = []

    for ir in function.all_slithir_operations():
        if isinstance(ir, LibraryCall):

            # We look if one of the target is used as an argument of the library
            # For example in:
            #   - do_check(address some_name) is a library definition
            #   - myLib.do_check(param) is library call
            # If param is a target, we then call _targets_checked_directly, where targets is [some_name]
            # We then relive "param" from our target if "some_name" wes checked

            # new_targets maps the lib parameter <> target
            # Note this is not robust if the target is first copied another variable
            # But this probably never happens
            new_targets: Dict[Variable, Variable] = {}
            for idx, param in enumerate(ir.arguments):
                for target in targets:
                    if param == target:
                        new_targets[ir.function.parameters[idx]] = target

            if new_targets:
                new_targets_keys = list(new_targets.keys())
                to_be_removed = _targets_checked_directly(ir.function, new_targets_keys)
                for new_target in to_be_removed:
                    vars_removed.append(new_targets[new_target])

    return vars_removed


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

    def _detect(self) -> List[Output]:
        """Detect if addresses are zero address validated before use.
        Returns:
            list: {'(function, node)'}
        """

        results: List[Output] = []

        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions_entry_points:
                targets: List[Variable] = [
                    param
                    for param in function.parameters
                    if param.type == ElementaryType("address")
                ]

                to_be_removed = _targets_checked_directly(function, targets)
                targets = [t for t in targets if t not in to_be_removed]
                if targets:
                    to_be_removed = _targets_checked_in_lib(function, targets)
                    targets = [t for t in targets if t not in to_be_removed]

                # missing_zero_address_validation = set(targets) - set(removed)
                for var in targets:
                    info = [var, " lacks a zero check\n"]
                    res = self.generate_result(info)
                    results.append(res)

        return results
