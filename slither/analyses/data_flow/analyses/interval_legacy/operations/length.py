"""Handler for Length operations (array/bytes length access) in interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.length import Length
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
        TrackedSMTVariable,
    )
    from slither.core.cfg.node import Node


class LengthHandler(BaseOperationHandler):
    """Handle Length operations: actual length for constants, full uint256 range otherwise."""

    def handle(
        self,
        operation: Optional[Length],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if not self._validate_operation(operation, domain):
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        if lvalue_name is None:
            return

        result_type = ElementaryType("uint256")
        lvalue_var = self._get_or_create_lvalue_var(lvalue_name, result_type, domain)
        if lvalue_var is None:
            return

        # Try to constrain to constant length, otherwise leave dynamic
        if self._try_constrain_constant(operation.value, lvalue_var):
            return
        if self._try_constrain_from_metadata(operation.value, lvalue_var, domain):
            return

        self.logger.debug(
            "Handled length operation: LENGTH {value} -> {lvalue} (dynamic range)",
            value=operation.value,
            lvalue=lvalue_name,
        )

    def _validate_operation(
        self, operation: Optional[Length], domain: "IntervalDomain"
    ) -> bool:
        """Validate the operation can be processed."""
        if operation is None or not isinstance(operation, Length):
            return False
        if self.solver is None:
            return False
        if domain.variant != DomainVariant.STATE:
            return False
        if operation.lvalue is None:
            return False
        return True

    def _get_or_create_lvalue_var(
        self,
        lvalue_name: str,
        result_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> Optional["TrackedSMTVariable"]:
        """Get or create tracked variable for the length result."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if tracked is not None:
            return tracked

        tracked = IntervalSMTUtils.create_tracked_variable(
            self.solver, lvalue_name, result_type
        )
        if tracked is None:
            return None

        domain.state.set_range_variable(lvalue_name, tracked)
        tracked.assert_no_overflow(self.solver)
        return tracked

    def _try_constrain_constant(
        self, value: object, lvalue_var: "TrackedSMTVariable"
    ) -> bool:
        """Try to constrain length from a constant value. Returns True if handled."""
        if not isinstance(value, Constant):
            return False

        const_value = value.value
        actual_length: Optional[int] = None

        if isinstance(const_value, (bytes, str)):
            actual_length = len(const_value)
        elif isinstance(const_value, (list, tuple)):
            actual_length = len(const_value)

        if actual_length is None:
            return False

        const_term: SMTTerm = self.solver.create_constant(actual_length, lvalue_var.sort)
        constraint: SMTTerm = lvalue_var.term == const_term
        self.solver.assert_constraint(constraint)
        self.logger.debug("Constrained length of constant to {length}", length=actual_length)
        return True

    def _try_constrain_from_metadata(
        self,
        value: object,
        lvalue_var: "TrackedSMTVariable",
        domain: "IntervalDomain",
    ) -> bool:
        """Try to constrain length from variable metadata. Returns True if handled."""
        value_name = IntervalSMTUtils.resolve_variable_name(value)
        if value_name is None:
            return False

        value_tracked = self._find_value_tracked(value_name, domain)
        if value_tracked is None:
            return False

        bytes_length = value_tracked.base.metadata.get("bytes_length")
        if bytes_length is None:
            return False

        const_term: SMTTerm = self.solver.create_constant(bytes_length, lvalue_var.sort)
        constraint: SMTTerm = lvalue_var.term == const_term
        self.solver.assert_constraint(constraint)
        self.logger.debug(
            "Constrained length from metadata: {value} has length {length}",
            value=value_name,
            length=bytes_length,
        )
        return True

    def _find_value_tracked(
        self, value_name: str, domain: "IntervalDomain"
    ) -> Optional["TrackedSMTVariable"]:
        """Find tracked variable for value, trying SSA variants if needed."""
        tracked = IntervalSMTUtils.get_tracked_variable(domain, value_name)
        if tracked is not None:
            return tracked

        # Try prefix-based lookup for SSA-versioned variables
        candidate_vars = domain.state.get_variables_by_prefix(value_name + "|")
        for var_name in candidate_vars:
            tracked = domain.state.range_variables.get(var_name)
            if tracked is not None:
                return tracked

        return None
