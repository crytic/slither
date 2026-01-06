"""Handler for the `timestamp()` Solidity builtin in interval analysis."""

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

# Timestamp bounds: reasonable range for block.timestamp
# Min: Jan 1, 2020 (1577836800) - reasonable past bound
# Max: Jan 1, 2125 (~4891881600) - about 100 years from now
TIMESTAMP_MIN = 1577836800
TIMESTAMP_MAX = 4891881600


class TimestampHandler(BaseOperationHandler):
    """Handle `timestamp()`, modeling block.timestamp as a uint256 within a reasonable time range."""

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

        # timestamp() returns uint256
        return_type = ElementaryType("uint256")

        # Fetch existing tracked variable if present
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is None:
            # Create a fresh tracked variable for the timestamp result
            tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                lvalue_name,
                return_type,
            )
            # Guard: creation may fail for unsupported types
            if tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, tracked)

        # Constrain timestamp to reasonable bounds [2020, 2125]
        min_const = self.solver.create_constant(TIMESTAMP_MIN, tracked.sort)
        max_const = self.solver.create_constant(TIMESTAMP_MAX, tracked.sort)

        # Assert: TIMESTAMP_MIN <= timestamp <= TIMESTAMP_MAX
        self.solver.assert_constraint(self.solver.bv_uge(tracked.term, min_const))
        self.solver.assert_constraint(self.solver.bv_ule(tracked.term, max_const))

        # Timestamps don't overflow
        tracked.assert_no_overflow(self.solver)
