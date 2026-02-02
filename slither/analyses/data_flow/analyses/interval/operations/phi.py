"""Phi operation handler for interval analysis."""

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
from slither.slithir.operations.phi import Phi

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node


class PhiHandler(BaseOperationHandler):
    """Handler for Phi operations in SSA form.

    Phi nodes merge values from different control flow paths. In Slither's
    interprocedural SSA, function entry Phi nodes merge values from ALL
    call sites.

    Strategy:
    1. If lvalue already tracked (e.g., from parameter binding) -> preserve it
    2. If rvalues are tracked -> create variable equal to one of them (disjunction)
    3. If no rvalues tracked -> create unconstrained variable
    """

    def handle(
        self,
        operation: Phi,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process Phi operation by merging incoming values."""
        if operation.lvalue is None:
            return

        lvalue_type = operation.lvalue.type
        if not isinstance(lvalue_type, ElementaryType):
            return

        result_name = get_variable_name(operation.lvalue)

        # If already tracked (from parameter binding), preserve those constraints
        existing = domain.state.get_variable(result_name)
        if existing is not None:
            return

        # Get tracked variables for incoming values
        incoming_vars = self._get_incoming_variables(operation.rvalues, domain)

        # Create the result variable
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
        """Get tracked variables for Phi incoming values."""
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
        """Add constraint that result equals one of the incoming values.

        For single incoming: result == v1
        For multiple: result == v1 OR result == v2 OR ...
        """
        if len(incoming_vars) == 1:
            self.solver.assert_constraint(result_var.term == incoming_vars[0].term)
            return

        # Multiple incoming values - create disjunction
        equalities = [result_var.term == var.term for var in incoming_vars]
        disjunction = self.solver.Or(*equalities)

        self.solver.assert_constraint(disjunction)
