"""Phi operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

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
    from slither.analyses.data_flow.analyses.interval.analysis.loop import (
        IntervalLoopMetadata,
    )
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.analyses.data_flow.analyses.interval.core.state import State
    from slither.core.cfg.node import Node
    from slither.slithir.operations.operation import Operation
    from slither.slithir.utils.utils import LVALUE, RVALUE
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver

from slither.analyses.data_flow.smt_solver.facts import LoopHeaderId


class PhiHandler(BaseOperationHandler):
    """Handler for Phi operations in SSA form.

    Phi nodes merge values from different control flow paths. In Slither's
    interprocedural SSA, function entry Phi nodes merge values from ALL
    call sites.

    Loop-header values are recomputed from the currently reachable incoming SSA
    alternatives. The loop fixpoint owns widening and generation state.
    """

    def __init__(self, solver: SMTSolver) -> None:
        super().__init__(solver)
        self._loop_metadata: IntervalLoopMetadata | None = None

    def configure_loop_metadata(self, metadata: IntervalLoopMetadata) -> None:
        """Bind traversal-independent loop SSA classifications."""
        self._loop_metadata = metadata

    def handle(
        self,
        operation: Operation,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Process Phi operation by merging incoming values."""
        operation, state = self._require_phi_state(operation, domain)
        if operation.lvalue is None:
            return

        lvalue_type = operation.lvalue.type
        if not isinstance(lvalue_type, ElementaryType):
            return

        result_name = get_variable_name(cast("LVALUE", operation.lvalue))
        is_loop_header = self._is_loop_header(node)

        if is_loop_header:
            self._handle_loop_header_phi(operation, domain, node, result_name, lvalue_type)
            return

        # If already tracked (from parameter binding), preserve those constraints
        existing = state.get_variable(result_name)
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

        state.set_variable(result_name, result_variable)

    def _is_loop_header(self, node: Node) -> bool:
        """Use natural-loop metadata when the engine has prepared the handler."""
        if self._loop_metadata is None:
            return node.type is NodeType.IFLOOP
        return self._loop_metadata.is_loop_header(LoopHeaderId.from_node(node))

    @staticmethod
    def _require_phi_state(
        operation: Operation,
        domain: IntervalDomain,
    ) -> tuple[Phi, State]:
        """Validate the registry dispatch and concrete transfer state."""
        if not isinstance(operation, Phi):
            raise TypeError("PhiHandler requires a Phi operation")
        state = domain.state
        if state is None:
            raise ValueError("Phi transfer requires a concrete interval state")
        return operation, state

    @staticmethod
    def _incoming_interval(incoming: list[TrackedSMTVariable]) -> NumericInterval:
        """Return the interval hull of all tracked phi alternatives."""
        interval = incoming[0].interval
        for variable in incoming[1:]:
            interval = interval.hull(variable.interval)
        return interval

    def _handle_loop_header_phi(
        self,
        operation: Phi,
        domain: IntervalDomain,
        node: Node,
        result_name: str,
        lvalue_type: ElementaryType,
    ) -> None:
        """Recompute a loop phi without creating a cyclic immutable equation."""
        state = domain.state
        if state is None:
            raise ValueError("Loop phi transfer requires a concrete interval state")
        sort = type_to_sort(lvalue_type)
        is_signed = is_signed_type(lvalue_type)
        bit_width = get_bit_width(lvalue_type)
        result_variable = TrackedSMTVariable.create(
            self.solver, result_name, sort, is_signed=is_signed, bit_width=bit_width
        )
        incoming = self._active_loop_incoming(operation, domain, node, result_name)
        if incoming:
            result_variable = result_variable.with_interval(
                self._incoming_interval(incoming),
                is_total=True,
            )
        state.set_variable(result_name, result_variable)

    def _active_loop_incoming(
        self,
        operation: Phi,
        domain: IntervalDomain,
        node: Node,
        result_name: str,
    ) -> list[TrackedSMTVariable]:
        """Resolve every currently active phi alternative or return no precision."""
        state = domain.state
        if state is None:
            raise ValueError("Loop phi lookup requires a concrete interval state")
        if self._loop_metadata is None:
            incoming = self._get_incoming_variables(operation.rvalues, domain)
            return incoming if len(incoming) == len(operation.rvalues) else []
        bindings = self._loop_metadata.variables_for(LoopHeaderId.from_node(node))
        binding = next((item for item in bindings if item.header_name == result_name), None)
        if binding is None:
            return []
        active_names = binding.entry_names
        if state.get_variable(result_name) is not None:
            active_names = (*active_names, *binding.back_names)
        incoming = [state.get_variable(name) for name in active_names]
        if any(variable is None for variable in incoming):
            return []
        return [variable for variable in incoming if variable is not None]

    def _get_incoming_variables(
        self,
        rvalues: list[RVALUE],
        domain: IntervalDomain,
    ) -> list[TrackedSMTVariable]:
        """Get tracked variables for Phi incoming values."""
        state = domain.state
        if state is None:
            raise ValueError("Phi input lookup requires a concrete interval state")
        tracked_variables = []
        for rvalue in rvalues:
            rvalue_name = get_variable_name(rvalue)
            tracked = state.get_variable(rvalue_name)
            if tracked is not None:
                tracked_variables.append(tracked)
        return tracked_variables

    def _get_equation_variables(
        self,
        rvalues: list[RVALUE],
        domain: IntervalDomain,
    ) -> list[TrackedSMTVariable]:
        """Return all static phi alternatives, declaring absent symbols locally."""
        state = domain.state
        if state is None:
            raise ValueError("Phi equation lookup requires a concrete interval state")
        variables = []
        for rvalue in rvalues:
            name = get_variable_name(rvalue)
            tracked = state.get_variable(name)
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
