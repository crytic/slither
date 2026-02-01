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
    """Handle `calldataload(uint256)`, modeling 32-byte calldata read as unconstrained uint256."""

    def handle(
        self,
        operation: Optional[SolidityCall],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if not self._validate_preconditions(operation, domain):
            return

        lvalue_name, return_type = self._resolve_lvalue_info(operation)
        if lvalue_name is None or return_type is None:
            return

        tracked = self._get_or_create_tracked(domain, lvalue_name, return_type)
        if tracked is None:
            return

        self._track_as_attacker_controlled(lvalue_name)
        tracked.assert_no_overflow(self.solver)

    def _validate_preconditions(
        self, operation: Optional[SolidityCall], domain: "IntervalDomain"
    ) -> bool:
        """Validate operation, solver, and domain state."""
        if operation is None or not isinstance(operation, SolidityCall):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        return True

    def _resolve_lvalue_info(
        self, operation: SolidityCall
    ) -> tuple[Optional[str], Optional[ElementaryType]]:
        """Resolve lvalue name and return type from operation."""
        lvalue = operation.lvalue
        if lvalue is None:
            return None, None

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            return None, None

        return_type = self._resolve_return_type(operation, lvalue)
        if return_type is None or IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            return None, None

        return lvalue_name, return_type

    def _resolve_return_type(self, operation: SolidityCall, lvalue) -> Optional[ElementaryType]:
        """Resolve return type from operation or lvalue."""
        type_call = getattr(operation, "type_call", None)
        if isinstance(type_call, list) and type_call:
            resolved = IntervalSMTUtils.resolve_elementary_type(type_call[0])
            if resolved is not None:
                return resolved

        if hasattr(lvalue, "type"):
            return IntervalSMTUtils.resolve_elementary_type(lvalue.type)
        return None

    def _get_or_create_tracked(
        self, domain: "IntervalDomain", lvalue_name: str, return_type: ElementaryType
    ):
        """Get existing or create new tracked variable."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(self.solver, lvalue_name, return_type)
        if tracked is None:
            return None
        domain.state.set_range_variable(lvalue_name, tracked)
        return tracked

    def _track_as_attacker_controlled(self, lvalue_name: str) -> None:
        """Track this variable as attacker-controlled for safety analysis."""
        if self.analysis is not None:
            self.analysis.safety_context.calldata_variables.add(lvalue_name)
            self.logger.debug(
                "Tracking calldata variable as attacker-controlled: {var_name}",
                var_name=lvalue_name,
            )
