"""Handler for condition operations."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.slithir.operations.condition import Condition

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class ConditionHandler(BaseOperationHandler):
    """Handler for condition operations (if/else conditions)."""

    def handle(
        self,
        operation: Optional[Condition],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Handle condition operation"""
        pass
