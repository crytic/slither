"""PhiCallback operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_bit_width,
    get_variable_name,
    is_signed_type,
    type_to_sort,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.phi_callback import PhiCallback


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class PhiCallbackHandler(BaseOperationHandler):
    """Handler for PhiCallback operations.

    PhiCallback is a special Phi node for state variables after external calls
    that might have callbacks (reentrancy). Since external calls can trigger
    arbitrary state changes, we treat the result as unconstrained.

    This is a sound over-approximation: after an external call, state variables
    could have any value within their type range due to potential callbacks.
    """

    def handle(
        self,
        operation: PhiCallback,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Process PhiCallback by creating unconstrained state variable."""
        if operation.lvalue is None:
            return

        lvalue_type = operation.lvalue.type
        if not isinstance(lvalue_type, ElementaryType):
            return

        result_name = get_variable_name(operation.lvalue)

        # If already tracked, preserve existing constraints
        existing = domain.state.get_variable(result_name)
        if existing is not None:
            return

        # Get tracked variables for incoming values
        incoming_vars = self._get_incoming_variables(operation.rvalues, domain)

        sort = type_to_sort(lvalue_type)
        is_signed = is_signed_type(lvalue_type)
        bit_width = get_bit_width(lvalue_type)

        result_var = TrackedSMTVariable.create(
            self.solver, result_name, sort, is_signed=is_signed, bit_width=bit_width
        )

        equation_vars = self._get_equation_variables(operation.rvalues, domain)
        if incoming_vars:
            result_var = result_var.with_interval(
                self._incoming_interval(incoming_vars),
                is_total=len(incoming_vars) == len(operation.rvalues),
            )
        if equation_vars:
            self._add_phi_constraints(
                operation,
                node,
                domain,
                result_var,
                equation_vars,
            )

        domain.state.set_variable(result_name, result_var)

    @staticmethod
    def _incoming_interval(incoming: list[TrackedSMTVariable]) -> NumericInterval:
        """Return the interval hull of all tracked callback alternatives."""
        interval = incoming[0].interval
        for variable in incoming[1:]:
            interval = interval.hull(variable.interval)
        return interval

    def _get_incoming_variables(
        self,
        rvalues: list,
        domain: IntervalDomain,
    ) -> list[TrackedSMTVariable]:
        """Get tracked variables for PhiCallback incoming values."""
        tracked_vars = []
        for rvalue in rvalues:
            rvalue_name = get_variable_name(rvalue)
            tracked = domain.state.get_variable(rvalue_name)
            if tracked is not None:
                tracked_vars.append(tracked)
        return tracked_vars

    def _get_equation_variables(
        self,
        rvalues: list,
        domain: IntervalDomain,
    ) -> list[TrackedSMTVariable]:
        """Return every static callback alternative independent of arrival order."""
        variables = []
        for rvalue in rvalues:
            name = get_variable_name(rvalue)
            tracked = domain.state.get_variable(name)
            value_type = getattr(rvalue, "type", None)
            if tracked is None and isinstance(value_type, ElementaryType):
                tracked = TrackedSMTVariable.create(
                    self.solver,
                    name,
                    type_to_sort(value_type),
                    is_signed=is_signed_type(value_type),
                    bit_width=get_bit_width(value_type),
                )
            if tracked is not None:
                variables.append(tracked)
        return variables

    def _add_phi_constraints(
        self,
        operation: PhiCallback,
        node: Node,
        domain: IntervalDomain,
        result_var: TrackedSMTVariable,
        incoming_vars: list[TrackedSMTVariable],
    ) -> None:
        """Add constraint that result equals one of the incoming values."""
        if len(incoming_vars) == 1:
            self._register_equation(
                operation,
                node,
                domain,
                result_var.term == incoming_vars[0].term,
                "phi_callback_result",
            )
            return

        # Multiple incoming values - create disjunction
        equalities = [result_var.term == var.term for var in incoming_vars]
        disjunction = self.solver.Or(*equalities)

        self._register_equation(
            operation,
            node,
            domain,
            disjunction,
            "phi_callback_result",
        )
