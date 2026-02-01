"""Shared type utilities for interval analysis operation handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint, Byte

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.slithir.utils.utils import LVALUE, RVALUE

logger = get_logger()


def get_variable_name(variable: "LVALUE | RVALUE") -> str:
    """Get the SSA name for a variable, falling back to regular name."""
    ssa_name = getattr(variable, "ssa_name", None)
    if ssa_name is not None:
        return ssa_name
    return variable.name


def is_signed_type(element_type: ElementaryType) -> bool:
    """Check if the Solidity type is a signed integer."""
    return element_type.type in Int


def get_bit_width(element_type: ElementaryType) -> int:
    """Get bit width for a Solidity elementary type."""
    type_string = element_type.type

    if type_string in Uint or type_string in Int:
        return _int_bit_width(type_string)
    if type_string == "bool":
        return 1
    if type_string in ("address", "address payable"):
        return 160
    if type_string in Byte:
        return _byte_bit_width(type_string)
    return 256


def _int_bit_width(type_string: str) -> int:
    """Get bit width for integer type (uint* or int*)."""
    if type_string in ("uint", "int"):
        return 256
    if type_string.startswith("uint"):
        return int(type_string[4:])
    if type_string.startswith("int"):
        return int(type_string[3:])
    return 256


def _byte_bit_width(type_string: str) -> int:
    """Get bit width for bytes type (bytes* or byte)."""
    if type_string == "bytes":
        return 256
    if type_string == "byte":
        return 8
    return int(type_string[5:]) * 8


def type_to_sort(element_type: ElementaryType) -> Sort:
    """Convert Solidity elementary type to SMT sort.

    Args:
        element_type: The Solidity elementary type.

    Returns:
        The corresponding SMT sort.

    Raises:
        NotImplementedError: If the type is not supported.
    """
    type_string = element_type.type

    if type_string in Uint or type_string in Int:
        width = _int_bit_width(type_string)
        return Sort(kind=SortKind.BITVEC, parameters=[width])

    if type_string == "bool":
        return Sort(kind=SortKind.BITVEC, parameters=[1])

    if type_string in ("address", "address payable"):
        return Sort(kind=SortKind.BITVEC, parameters=[160])

    if type_string in Byte:
        width = _byte_bit_width(type_string)
        return Sort(kind=SortKind.BITVEC, parameters=[width])

    supported_types = "uint*, int*, bool, address, address payable, bytes*"
    logger.error_and_raise(
        f"Unsupported type '{type_string}'. Supported: {supported_types}",
        NotImplementedError,
    )


def constant_to_term(
    solver: "SMTSolver",
    value: int | bool,
    bit_width: int,
) -> SMTTerm:
    """Convert a constant value to an SMT bitvector term.

    Args:
        solver: The SMT solver instance.
        value: The constant value (int or bool).
        bit_width: The bit width for the resulting term.

    Returns:
        The SMT term representing the constant.
    """
    int_value = 1 if value is True else (0 if value is False else value)
    sort = Sort(kind=SortKind.BITVEC, parameters=[bit_width])
    return solver.create_constant(int_value, sort)
