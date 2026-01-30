"""Handler for low-level EVM call opcodes in interval analysis.

Handles: call, staticcall, delegatecall, callcode
These opcodes return a boolean success value (0 or 1).
"""

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


class LowLevelCallHandler(BaseOperationHandler):
    """Handle low-level EVM call opcodes (call, staticcall, delegatecall, callcode).

    These opcodes return a boolean success value represented as uint256 (0 or 1).
    Since the target function is unknown at compile time, we treat the return
    value as unconstrained within its type bounds.
    """

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: IntervalDomain,
        node: "Node",
    ) -> None:
        if operation is None:
            return

        self.logger.debug("Handling low-level call: {operation}", operation=operation)

        if not self._validate_preconditions(domain):
            return

        lvalue_name, return_type = self._resolve_lvalue_info(operation)
        if lvalue_name is None or return_type is None:
            return

        self._get_or_create_tracked(domain, lvalue_name, return_type)
        self.logger.debug(
            "Created unconstrained return variable for low-level call: {lvalue}",
            lvalue=lvalue_name,
        )

    def _validate_preconditions(self, domain: IntervalDomain) -> bool:
        """Validate solver and domain state."""
        if self.solver is None:
            self.logger.warning("Solver is None, skipping low-level call")
            return False
        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping low-level call")
            return False
        return True

    def _resolve_lvalue_info(
        self, operation: SolidityCall
    ) -> tuple[Optional[str], Optional[ElementaryType]]:
        """Resolve lvalue name and return type from operation."""
        lvalue = operation.lvalue
        if lvalue is None:
            self.logger.debug("Low-level call has no lvalue, nothing to track")
            return None, None

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            self.logger.debug("Could not resolve lvalue name for low-level call")
            return None, None

        return_type = self._resolve_return_type(lvalue)
        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            self.logger.debug(
                "Unsupported return type for low-level call: {type}", type=return_type
            )
            return None, None

        return lvalue_name, return_type

    def _resolve_return_type(self, lvalue) -> ElementaryType:
        """Resolve return type from lvalue, defaulting to bool."""
        if hasattr(lvalue, "type"):
            resolved = IntervalSMTUtils.resolve_elementary_type(lvalue.type)
            if resolved is not None:
                return resolved
        return ElementaryType("bool")

    def _get_or_create_tracked(
        self, domain: IntervalDomain, lvalue_name: str, return_type: ElementaryType
    ) -> None:
        """Get existing or create new tracked variable."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is None:
            tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            if tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, tracked)
            tracked.assert_no_overflow(self.solver)
