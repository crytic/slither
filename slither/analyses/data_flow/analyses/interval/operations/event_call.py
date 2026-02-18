"""Event call operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.event_call import EventCall

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class EventCallHandler(BaseOperationHandler):
    """Handler for event emissions.

    Events emit log data but produce no lvalue and don't modify
    contract state, so this handler is a no-op.
    """

    def handle(
        self,
        operation: EventCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """No-op: event emissions don't affect interval state."""
