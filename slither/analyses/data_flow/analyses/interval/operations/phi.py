"""Phi operation handler for interval analysis."""

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
from slither.core.cfg.node import NodeType
from slither.core.solidity_types.elementary_type import ElementaryType
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
        domain: IntervalDomain,
        node: Node,
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

        equation_variables = self._get_equation_variables(operation.rvalues, domain)
        if incoming_variables:
            result_variable = result_variable.with_interval(
                self._incoming_interval(incoming_variables),
                is_total=len(incoming_variables) == len(operation.rvalues),
            )
        if equation_variables:
            self._add_phi_constraints(
                operation,
                node,
                domain,
                result_variable,
                equation_variables,
            )

        domain.state.set_variable(result_name, result_variable)

    @staticmethod
    def _incoming_interval(incoming: list[TrackedSMTVariable]) -> NumericInterval:
        """Return the interval hull of all tracked phi alternatives."""
        interval = incoming[0].interval
        for variable in incoming[1:]:
            interval = interval.hull(variable.interval)
        return interval

    def _handle_loop_header_phi(
        self,
        domain: IntervalDomain,
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
        rvalues: list[RVALUE],
        domain: IntervalDomain,
    ) -> list[TrackedSMTVariable]:
        """Get tracked variables for Phi incoming values."""
        tracked_variables = []
        for rvalue in rvalues:
            rvalue_name = get_variable_name(rvalue)
            tracked = domain.state.get_variable(rvalue_name)
            if tracked is not None:
                tracked_variables.append(tracked)
        return tracked_variables

    def _get_equation_variables(
        self,
        rvalues: list[RVALUE],
        domain: IntervalDomain,
    ) -> list[TrackedSMTVariable]:
        """Return all static phi alternatives, declaring absent symbols locally."""
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
        operation: Phi,
        node: Node,
        domain: IntervalDomain,
        result_variable: TrackedSMTVariable,
        incoming_variables: list[TrackedSMTVariable],
    ) -> None:
        """Add constraint that result equals one of the incoming values.

        For single incoming: result == v1
        For multiple: result == v1 OR result == v2 OR ...
        """
        if len(incoming_variables) == 1:
            self._register_equation(
                operation,
                node,
                domain,
                result_variable.term == incoming_variables[0].term,
                "phi_result",
            )
            return

        # Multiple incoming values - create disjunction
        equalities = [result_variable.term == variable.term for variable in incoming_variables]
        disjunction = self.solver.Or(*equalities)

        self._register_equation(
            operation,
            node,
            domain,
            disjunction,
            "phi_result",
        )
