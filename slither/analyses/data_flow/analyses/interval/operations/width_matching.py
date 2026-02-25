"""BitVec width matching for SMT terms."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.smt_solver.types import SMTTerm

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


def match_width_to_int(
    solver: "SMTSolver",
    source_term: SMTTerm,
    target_width: int,
) -> SMTTerm:
    """Match source term width to a target bit width.

    Truncates (extracts low bits) when source is wider than target,
    zero-extends when source is narrower.

    Args:
        solver: SMT solver instance for bitvector operations.
        source_term: The term to convert.
        target_width: The target bit width.

    Returns:
        source_term adjusted to the target bit width.
    """
    source_width = solver.bv_size(source_term)

    if source_width == target_width:
        return source_term
    if source_width > target_width:
        return solver.bv_extract(source_term, target_width - 1, 0)
    return solver.bv_zero_ext(source_term, target_width - source_width)


def match_width(
    solver: "SMTSolver",
    source_term: SMTTerm,
    target_term: SMTTerm,
) -> SMTTerm:
    """Match source term width to target term width.

    Args:
        solver: SMT solver instance for bitvector operations.
        source_term: The term to convert.
        target_term: The term whose width to match.

    Returns:
        source_term adjusted to match target_term's bit width.
    """
    target_width = solver.bv_size(target_term)
    return match_width_to_int(solver, source_term, target_width)
