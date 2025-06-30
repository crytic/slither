from decimal import Decimal
from typing import Optional
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary
from slither.slithir.variables.temporary import TemporaryVariable

UINT256_MAX = Decimal(
    "115792089237316195423570985008687907853269984665640564039457584007913129639935"
)
INT256_MAX = Decimal(
    "57896044618658097711785492504343953926634992332820282019728792003956564819967"
)
INT256_MIN = Decimal(
    "-57896044618658097711785492504343953926634992332820282019728792003956564819968"
)


def _is_numeric_type(elementary_type: ElementaryType) -> bool:
    """Check if type is numeric."""
    if not elementary_type:
        return False
    type_name = elementary_type.name
    return (
        type_name.startswith("int")
        or type_name.startswith("uint")
        or type_name.startswith("fixed")
        or type_name.startswith("ufixed")
    )


def _get_type_bounds_for_elementary_type(elem_type: ElementaryType) -> tuple[Decimal, Decimal]:
    """Get min/max bounds for elementary type."""
    type_name = elem_type.name

    if type_name.startswith("uint"):
        return _get_uint_bounds(type_name)
    elif type_name.startswith("int"):
        return _get_int_bounds(type_name)

    return Decimal("0"), UINT256_MAX


def _get_uint_bounds(type_name: str) -> tuple[Decimal, Decimal]:
    """Get bounds for unsigned integer types."""
    if type_name == "uint" or type_name == "uint256":
        return Decimal("0"), UINT256_MAX

    try:
        bits = int(type_name[4:])
        max_val = (2**bits) - 1
        return Decimal("0"), Decimal(str(max_val))
    except ValueError:
        return Decimal("0"), UINT256_MAX


def _get_int_bounds(type_name: str) -> tuple[Decimal, Decimal]:
    """Get bounds for signed integer types."""
    if type_name == "int" or type_name == "int256":
        return INT256_MIN, INT256_MAX

    try:
        bits = int(type_name[3:])
        max_val = (2 ** (bits - 1)) - 1
        min_val = -(2 ** (bits - 1))
        return Decimal(str(min_val)), Decimal(str(max_val))
    except ValueError:
        return INT256_MIN, INT256_MAX


def _get_promotion_type(type1: ElementaryType, type2: ElementaryType) -> ElementaryType:
    """Get the promoted type from two elementary types."""
    size1 = _get_type_size(type1)
    size2 = _get_type_size(type2)
    return type1 if size1 >= size2 else type2


def _get_type_size(elem_type: ElementaryType) -> int:
    """Get the bit size of an elementary type."""
    type_name = elem_type.name

    if type_name.startswith("uint"):
        if type_name == "uint" or type_name == "uint256":
            return 256
        try:
            return int(type_name[4:])
        except ValueError:
            return 256
    elif type_name.startswith("int"):
        if type_name == "int" or type_name == "int256":
            return 256
        try:
            return int(type_name[3:])
        except ValueError:
            return 256
    return 256


def _create_interval_from_type(var_type: ElementaryType, min_val, max_val) -> IntervalInfo:
    """Create interval from type with min/max bounds."""
    return IntervalInfo(
        upper_bound=Decimal(str(max_val)),
        lower_bound=Decimal(str(min_val)),
        var_type=var_type,
    )


def _determine_target_type(operation: Binary) -> Optional[ElementaryType]:
    """Determine the target type for the operation result."""
    target_type = getattr(operation.lvalue, "type", None)

    # For temporary variables, infer type from operands
    if target_type is None and isinstance(operation.lvalue, TemporaryVariable):
        left_type = _get_variable_type(operation.variable_left)
        right_type = _get_variable_type(operation.variable_right)

        if left_type and right_type:
            target_type = _get_promotion_type(left_type, right_type)
        elif left_type:
            target_type = left_type
        elif right_type:
            target_type = right_type

    return target_type


def _get_variable_type(variable) -> Optional[ElementaryType]:
    """Safely get variable type."""
    return getattr(variable, "type", None) if hasattr(variable, "type") else None
