"""Handler for the `calldatacopy(uint256,uint256,uint256)` Solidity builtin in interval analysis."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class CalldataCopyHandler(BaseOperationHandler):
    """Handle `calldatacopy(uint256,uint256,uint256)`, treating it as a no-op."""

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        # Guard: ensure we have a valid SolidityCall operation
        if operation is None or not isinstance(operation, SolidityCall):
            return

        # calldatacopy doesn't return a value and doesn't affect tracked variables
        # It just copies calldata to memory, which we don't track in interval analysis
        # So we can safely skip it (no-op)
        return
