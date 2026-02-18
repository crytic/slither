"""Revert operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.slithir.operations.solidity_call import SolidityCall

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

REVERT_FUNCTIONS = frozenset({
    "revert()",
    "revert(string)",
})


class RevertHandler(BaseOperationHandler):
    """Handler for revert() calls.

    Revert unconditionally terminates execution, so the domain is set
    to BOTTOM (unreachable). BOTTOM is absorbed at join points, preserving
    constraints from non-reverting branches.
    """

    def handle(
        self,
        operation: SolidityCall,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Mark domain as BOTTOM (unreachable after revert)."""
        if domain.variant != DomainVariant.STATE:
            return

        domain.variant = DomainVariant.BOTTOM
