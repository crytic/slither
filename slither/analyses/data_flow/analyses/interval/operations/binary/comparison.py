"""Comparison binary operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.binary import Binary, BinaryType

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

logger = get_logger()

COMPARISON_OPERATIONS = frozenset({
    BinaryType.LESS,
    BinaryType.GREATER,
    BinaryType.LESS_EQUAL,
    BinaryType.GREATER_EQUAL,
    BinaryType.EQUAL,
    BinaryType.NOT_EQUAL,
    BinaryType.ANDAND,
    BinaryType.OROR,
})


class ComparisonHandler(BaseOperationHandler):
    """Handler for comparison binary operations.

    Supports: <, >, <=, >=, ==, !=, &&, ||

    NOT YET IMPLEMENTED - raises NotImplementedError when called.
    """

    def handle(
        self,
        operation: Binary,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process comparison binary operation."""
        logger.error_and_raise(
            f"Comparison operation '{operation.type.value}' is not yet implemented",
            NotImplementedError,
        )
