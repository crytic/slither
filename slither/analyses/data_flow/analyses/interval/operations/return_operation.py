"""Return operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.return_operation import Return

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class ReturnHandler(BaseOperationHandler):
    """Handler for return operations."""

    def handle(
        self,
        operation: Return,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process return operation. Currently a no-op."""
        pass
