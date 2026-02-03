"""Assignment operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.utils.utils import LVALUE, RVALUE

from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_conversion import (
    match_width,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    is_signed_type,
    get_bit_width,
    type_to_sort,
    constant_to_term,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class AssignmentHandler(BaseOperationHandler):
    """Handler for assignment operations."""

    def handle(
        self,
        operation: Assignment,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process assignment operation."""
        lvalue: LVALUE = operation.lvalue
        lvalue_name = get_variable_name(lvalue)
        lvalue_type = self._get_elementary_type(lvalue, operation)
        if lvalue_type is None:
            return

        sort = type_to_sort(lvalue_type)
        signed = is_signed_type(lvalue_type)
        bit_width = get_bit_width(lvalue_type)
        tracked_lvalue = TrackedSMTVariable.create(
            self.solver, lvalue_name, sort, is_signed=signed, bit_width=bit_width
        )

        should_add_constraint = self._should_add_constraint(
            operation.rvalue, lvalue_name, domain
        )
        if should_add_constraint:
            self._process_rvalue(operation.rvalue, tracked_lvalue, lvalue_type, domain)
            self._record_dependency(operation.rvalue, lvalue_name, domain)

        domain.state.set_variable(lvalue_name, tracked_lvalue)

    def _record_dependency(
        self,
        rvalue: RVALUE | Function | TupleVariable,
        lvalue_name: str,
        domain: "IntervalDomain",
    ) -> None:
        """Record that lvalue depends on rvalue."""
        if isinstance(rvalue, Constant):
            return

        rvalue_name = get_variable_name(rvalue)
        rvalue_deps = domain.state.get_dependencies(rvalue_name)
        domain.state.add_dependency(lvalue_name, rvalue_name)
        domain.state.add_dependencies(lvalue_name, rvalue_deps)

    def _should_add_constraint(
        self,
        rvalue: RVALUE | Function | TupleVariable,
        lvalue_name: str,
        domain: "IntervalDomain",
    ) -> bool:
        """Determine if we should add the equality constraint.

        Skip only if adding the constraint would create a circular dependency.
        """
        if isinstance(rvalue, Constant):
            return True

        rvalue_name = get_variable_name(rvalue)
        return not domain.state.has_transitive_dependency(rvalue_name, lvalue_name)

    def _get_elementary_type(
        self,
        variable: LVALUE,
        operation: Assignment,
    ) -> ElementaryType | None:
        """Extract elementary type from variable or operation."""
        if isinstance(operation.variable_return_type, ElementaryType):
            return operation.variable_return_type
        if isinstance(variable.type, ElementaryType):
            return variable.type
        return None

    def _process_rvalue(
        self,
        rvalue: RVALUE | Function | TupleVariable,
        tracked_lvalue: TrackedSMTVariable,
        lvalue_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        """Process rvalue and assert equality constraint."""
        if isinstance(rvalue, Constant):
            self._handle_constant(rvalue, tracked_lvalue)
            return

        rvalue_name = get_variable_name(rvalue)
        self._handle_variable(rvalue_name, rvalue, tracked_lvalue, lvalue_type, domain)

    def _handle_constant(
        self,
        constant: Constant,
        tracked_lvalue: TrackedSMTVariable,
    ) -> None:
        """Handle constant rvalue."""
        value = constant.value
        if not isinstance(value, (int, bool)):
            return

        width = self.solver.bv_size(tracked_lvalue.term)
        const_term = constant_to_term(self.solver, value, width)
        self.solver.assert_constraint(tracked_lvalue.term == const_term)

    def _handle_variable(
        self,
        rvalue_name: str,
        rvalue: RVALUE,
        tracked_lvalue: TrackedSMTVariable,
        lvalue_type: ElementaryType,
        domain: "IntervalDomain",
    ) -> None:
        """Handle variable rvalue."""
        tracked_rvalue = domain.state.get_variable(rvalue_name)

        if tracked_rvalue is None:
            rvalue_type = rvalue.type if isinstance(rvalue.type, ElementaryType) else lvalue_type
            sort = type_to_sort(rvalue_type)
            signed = is_signed_type(rvalue_type)
            bit_width = get_bit_width(rvalue_type)
            tracked_rvalue = TrackedSMTVariable.create(
                self.solver, rvalue_name, sort, is_signed=signed, bit_width=bit_width
            )
            domain.state.set_variable(rvalue_name, tracked_rvalue)

        rvalue_term = match_width(self.solver, tracked_rvalue.term, tracked_lvalue.term)
        self.solver.assert_constraint(tracked_lvalue.term == rvalue_term)
