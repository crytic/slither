"""Shared type utilities for interval analysis operation handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.elementary_type import ElementaryType, Int, Uint, Byte

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
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


def constrain_to_value(
    solver: "SMTSolver",
    target: TrackedSMTVariable,
    source: object,
    domain: "IntervalDomain",
) -> None:
    """Constrain target to equal source value (shared assignment logic).

    Handles both constant and variable sources. Used by AssignmentHandler
    and SstoreHandler.

    Args:
        solver: The SMT solver instance.
        target: The target TrackedSMTVariable to constrain.
        source: The source value (Constant or SlithIR variable).
        domain: The interval domain for variable lookup.
    """
    from slither.slithir.variables.constant import Constant
    from slither.analyses.data_flow.analyses.interval.operations.type_conversion import (
        match_width,
    )

    if isinstance(source, Constant):
        value = source.value
        if isinstance(value, (int, bool)):
            bit_width = solver.bv_size(target.term)
            const_term = constant_to_term(solver, value, bit_width)
            solver.assert_constraint(target.term == const_term)
        return

    source_name = get_variable_name(source)
    tracked_source = domain.state.get_variable(source_name)

    if tracked_source is None:
        tracked_source = try_create_parameter_variable(solver, source, source_name, domain)

    if tracked_source is None:
        return

    source_term = match_width(solver, tracked_source.term, target.term)
    solver.assert_constraint(target.term == source_term)


def try_create_parameter_variable(
    solver: "SMTSolver",
    operand: "RVALUE",
    operand_name: str,
    domain: "IntervalDomain",
) -> TrackedSMTVariable | None:
    """Create a tracked variable for a function parameter if applicable.

    Args:
        solver: The SMT solver instance.
        operand: The operand to check.
        operand_name: The SSA name of the operand.
        domain: The interval domain to add the variable to.

    Returns:
        The created TrackedSMTVariable, or None if not a parameter.
    """
    non_ssa = getattr(operand, "non_ssa_version", None)
    if non_ssa is None:
        return None

    function = getattr(non_ssa, "function", None)
    if function is None:
        return None

    if non_ssa not in function.parameters:
        return None

    operand_type = operand.type
    if not isinstance(operand_type, ElementaryType):
        return None

    bit_width = get_bit_width(operand_type)
    signed = is_signed_type(operand_type)
    sort = Sort(kind=SortKind.BITVEC, parameters=[bit_width])

    tracked = TrackedSMTVariable.create(
        solver, operand_name, sort, is_signed=signed, bit_width=bit_width
    )
    domain.state.set_variable(operand_name, tracked)
    return tracked
