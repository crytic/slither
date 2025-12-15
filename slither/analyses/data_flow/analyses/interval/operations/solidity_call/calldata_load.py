"""Handler for the `calldataload(uint256)` Solidity builtin in interval analysis."""

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


class CalldataLoadHandler(BaseOperationHandler):
    """Handle `calldataload(uint256)`, modeling its 32-byte calldata read as an unconstrained uint256 within type bounds."""

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

        # Derive the return elementary type.
        return_type: Optional[ElementaryType] = None

        # Prefer the explicit type information from the SolidityCall itself.
        type_call = getattr(operation, "type_call", None)
        if isinstance(type_call, list) and type_call:
            candidate = type_call[0]
            return_type = IntervalSMTUtils.resolve_elementary_type(candidate)

        # Fallback to lvalue.type if needed.
        if return_type is None and hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        # Guard: skip if we still cannot determine a supported return type
        if return_type is None:
            return

        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            # Guard: unsupported type for interval tracking
            return

        # Fetch existing tracked variable if present.
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is None:
            # Create a fresh tracked variable for the calldataload result.
            tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver,
                lvalue_name,
                return_type,
            )
            # Guard: creation may fail for unsupported types
            if tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, tracked)

        # For now we do not add additional constraints: calldata contents are modelled
        # as an unconstrained value within the type bounds.
        tracked.assert_no_overflow(self.solver)
