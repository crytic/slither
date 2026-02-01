"""Handler for the `gas()` Solidity builtin in interval analysis."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class GasHandler(BaseOperationHandler):
    """Handle `gas()`, modeling gasleft() as a uint256 with full range."""

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        # Guard: ensure we have a valid SolidityCall operation
        if operation is None or not isinstance(operation, SolidityCall):
            return

        # Guard: solver is required to create SMT variables
        if self.solver is None:
            return

        # Guard: only update when we have a concrete state domain
        if domain.variant != DomainVariant.STATE:
            return

        lvalue = operation.lvalue
        # Guard: nothing to track if there is no lvalue for the call result
        if lvalue is None:
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        # Guard: skip if we cannot resolve a stable name
        if lvalue_name is None:
            return

        # gas() returns uint256 (remaining gas)
        return_type = ElementaryType("uint256")

        # Fetch existing tracked variable if present
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is None:
            # Create a fresh tracked variable for the gas result (full uint256 range)
            tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                lvalue_name,
                return_type,
            )
            # Guard: creation may fail for unsupported types
            if tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, tracked)

        # Gas values don't overflow
        tracked.assert_no_overflow(self.solver)
