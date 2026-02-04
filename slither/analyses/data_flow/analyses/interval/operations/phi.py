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
from slither.core.cfg.node import NodeType
from slither.slithir.operations.phi import Phi

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node
    from slither.slithir.utils.utils import RVALUE


class PhiHandler(BaseOperationHandler):
    """Handler for Phi operations in SSA form.

    Phi nodes merge values from different control flow paths. In Slither's
    interprocedural SSA, function entry Phi nodes merge values from ALL
    call sites.

    Strategy:
    1. If lvalue already tracked from parameter binding -> preserve it
    2. At loop headers: selective widening based on comparing incoming to existing
    3. If rvalues are tracked -> create variable equal to one of them (disjunction)
    4. If no rvalues tracked -> create unconstrained variable
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
        is_loop_header = node.type == NodeType.IFLOOP

        # At loop headers: create unconstrained (widening handled by apply_widening)
        if is_loop_header:
            self._handle_loop_header_phi(domain, result_name, lvalue_type)
            return

        # If already tracked (from parameter binding), preserve those constraints
        existing = domain.state.get_variable(result_name)
        if existing is not None:
            return

        # Get tracked variables for incoming values
        incoming_variables = self._get_incoming_variables(operation.rvalues, domain)

        # Create the result variable
        sort = type_to_sort(lvalue_type)
        is_signed = is_signed_type(lvalue_type)
        bit_width = get_bit_width(lvalue_type)

        result_variable = TrackedSMTVariable.create(
            self.solver, result_name, sort, is_signed=is_signed, bit_width=bit_width
        )

        # If we have incoming values, constrain result to be one of them
        if incoming_variables:
            self._add_phi_constraints(result_variable, incoming_variables)

        domain.state.set_variable(result_name, result_variable)

    def _handle_loop_header_phi(
        self,
        domain: "IntervalDomain",
        result_name: str,
        lvalue_type: ElementaryType,
    ) -> None:
        """Handle phi at loop header.

        Creates unconstrained variable. Selective widening is handled by
        apply_widening() on back edges.

        NOTE: We cannot add constraints here because SMT constraints are permanent.
        get_or_declare_const returns the same SMT variable, so constraints from
        earlier iterations accumulate. This makes loop exits unreachable if we
        constrain phi variables to incoming values.
        """
        sort = type_to_sort(lvalue_type)
        is_signed = is_signed_type(lvalue_type)
        bit_width = get_bit_width(lvalue_type)

        existing = domain.state.get_variable(result_name)

        # First iteration: create unconstrained variable
        if existing is None:
            result_variable = TrackedSMTVariable.create(
                self.solver, result_name, sort, is_signed=is_signed, bit_width=bit_width
            )
            domain.state.set_variable(result_name, result_variable)
            return

        # Later iterations: keep existing (widening handled by apply_widening)

    def _get_incoming_variables(
        self,
        rvalues: List["RVALUE"],
        domain: "IntervalDomain",
    ) -> List[TrackedSMTVariable]:
        """Get tracked variables for Phi incoming values."""
        tracked_variables = []
        for rvalue in rvalues:
            rvalue_name = get_variable_name(rvalue)
            tracked = domain.state.get_variable(rvalue_name)
            if tracked is not None:
                tracked_variables.append(tracked)
        return tracked_variables

    def _add_phi_constraints(
        self,
        result_variable: TrackedSMTVariable,
        incoming_variables: List[TrackedSMTVariable],
    ) -> None:
        """Add constraint that result equals one of the incoming values.

        For single incoming: result == v1
        For multiple: result == v1 OR result == v2 OR ...
        """
        if len(incoming_variables) == 1:
            self.solver.assert_constraint(
                result_variable.term == incoming_variables[0].term
            )
            return

        # Multiple incoming values - create disjunction
        equalities = [
            result_variable.term == variable.term for variable in incoming_variables
        ]
        disjunction = self.solver.Or(*equalities)

        self.solver.assert_constraint(disjunction)
