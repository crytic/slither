"""PhiCallback operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
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
        domain: "IntervalDomain",
        node: "Node",
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

        # If we have incoming values, constrain result to be one of them
        if incoming_vars:
            self._add_phi_constraints(result_var, incoming_vars)

        domain.state.set_variable(result_name, result_var)

    def _get_incoming_variables(
        self,
        rvalues: List,
        domain: "IntervalDomain",
    ) -> List[TrackedSMTVariable]:
        """Get tracked variables for PhiCallback incoming values."""
        tracked_vars = []
        for rvalue in rvalues:
            rvalue_name = get_variable_name(rvalue)
            tracked = domain.state.get_variable(rvalue_name)
            if tracked is not None:
                tracked_vars.append(tracked)
        return tracked_vars

    def _add_phi_constraints(
        self,
        result_var: TrackedSMTVariable,
        incoming_vars: List[TrackedSMTVariable],
    ) -> None:
        """Add constraint that result equals one of the incoming values."""
        if len(incoming_vars) == 1:
            self.solver.assert_constraint(result_var.term == incoming_vars[0].term)
            return

        # Multiple incoming values - create disjunction
        equalities = [result_var.term == var.term for var in incoming_vars]
        disjunction = self.solver.Or(*equalities)

        self.solver.assert_constraint(disjunction)
