"""Condition operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.slithir.operations.condition import Condition

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class ConditionHandler(BaseOperationHandler):
    """Handler for condition operations (if/else branching).

    The Condition operation marks the end of a conditional node.
    Branch-specific narrowing is handled by IntervalAnalysis.apply_condition,
    which is called by the engine for each branch.

    This handler is a no-op - it exists to register the operation type
    so the analysis doesn't throw NotImplementedError.
    """

    def handle(
        self,
        operation: Condition,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process condition operation (no-op).

        The actual branch filtering is done by the engine's apply_condition
        method, which calls IntervalAnalysis.apply_condition for each branch.
        """
        pass
