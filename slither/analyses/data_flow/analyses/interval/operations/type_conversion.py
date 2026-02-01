"""Type conversion operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.type_conversion import TypeConversion

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

logger = get_logger()


def match_width_to_int(
    solver: "SMTSolver",
    source_term: SMTTerm,
    target_width: int,
) -> SMTTerm:
    """Match source term width to a target bit width (truncate or extend).

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
    """Match source term width to target term width (truncate or extend).

    Args:
        solver: SMT solver instance for bitvector operations.
        source_term: The term to convert.
        target_term: The term whose width to match.

    Returns:
        source_term adjusted to match target_term's bit width.
    """
    target_width = solver.bv_size(target_term)
    return match_width_to_int(solver, source_term, target_width)


class TypeConversionHandler(BaseOperationHandler):
    """Handler for type conversion operations.

    NOT YET IMPLEMENTED - raises NotImplementedError when called.
    """

    def handle(
        self,
        operation: TypeConversion,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process type conversion operation."""
        logger.error_and_raise(
            f"TypeConversion to '{operation.type}' is not yet implemented",
            NotImplementedError,
        )
