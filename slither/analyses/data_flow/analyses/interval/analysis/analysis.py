"""Interval analysis implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_bit_width,
    get_variable_name,
    is_signed_type,
    type_to_sort,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.core.cfg.node import Node, NodeType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.types import SMTTerm
    from slither.core.variables.local_variable import LocalVariable

logger = get_logger()


class IntervalAnalysis(Analysis):
    """Forward interval analysis using SMT constraints."""

    def __init__(self, solver: SMTSolver) -> None:
        self._direction: Direction = Forward()
        self._solver: SMTSolver = solver
        self._registry: OperationHandlerRegistry = OperationHandlerRegistry(self._solver)

    @property
    def solver(self) -> SMTSolver:
        return self._solver

    def domain(self) -> Domain:
        return IntervalDomain.with_state(State({}))

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom()

    def transfer_function(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation | None,
    ) -> None:
        self._transfer_function_helper(node, domain, operation)

    def _transfer_function_helper(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation | None,
    ) -> None:
        if domain.variant == DomainVariant.TOP:
            return

        if domain.variant == DomainVariant.BOTTOM:
            if domain.state is not None:
                return  # Detected unreachable path - skip further processing
            self._initialize_domain_from_bottom(domain)

        self._handle_variable_declaration(node, domain)
        self._dispatch_operation(operation, domain, node)

    def _initialize_domain_from_bottom(self, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom."""
        domain.variant = DomainVariant.STATE
        domain.state = State({})

    def _handle_variable_declaration(
        self,
        node: Node,
        domain: IntervalDomain,
    ) -> None:
        """Handle variable declaration nodes by initializing to zero.

        In Solidity, uninitialized local variables have default zero values.
        This method processes NodeType.VARIABLE nodes that have no initializer,
        creating a tracked variable constrained to zero.
        """
        if node.type != NodeType.VARIABLE:
            return

        variable_declaration = node.variable_declaration
        if variable_declaration is None:
            return

        if not self._is_uninitialized_declaration(node, variable_declaration):
            return

        self._initialize_variable_to_zero(variable_declaration, domain)

    def _is_uninitialized_declaration(
        self,
        node: Node,
        variable: "LocalVariable",
    ) -> bool:
        """Check if a variable declaration has no initializer.

        Returns True if the variable is declared without an explicit value
        and the node has no SSA operations (which would indicate an initializer).
        """
        if node.irs_ssa:
            return False

        if not isinstance(variable.type, ElementaryType):
            return False

        return True

    def _initialize_variable_to_zero(
        self,
        variable: "LocalVariable",
        domain: IntervalDomain,
    ) -> None:
        """Create a tracked variable initialized to zero."""
        variable_type = variable.type
        if not isinstance(variable_type, ElementaryType):
            return

        variable_name = f"{variable.name}_0"
        sort = type_to_sort(variable_type)
        bit_width = get_bit_width(variable_type)
        signed = is_signed_type(variable_type)

        tracked = TrackedSMTVariable.create(
            self._solver, variable_name, sort, is_signed=signed, bit_width=bit_width
        )

        zero_term = self._solver.create_constant(0, sort)
        self._solver.assert_constraint(tracked.term == zero_term)

        domain.state.set_variable(variable_name, tracked)

    def _dispatch_operation(
        self,
        operation: Operation | None,
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Dispatch operation to appropriate handler."""
        if operation is None:
            return
        handler = self._registry.get_handler(type(operation))
        handler.handle(operation, domain, node)

    def apply_condition(
        self, domain: Domain, condition: Condition, branch_taken: bool
    ) -> Domain:
        """Apply branch-specific narrowing based on a condition.

        Looks up the comparison info stored by ComparisonHandler and
        adds the condition (or its negation) as a path constraint.

        Args:
            domain: The current abstract state.
            condition: The condition operation from the branch.
            branch_taken: True if then-branch (condition is true),
                          False if else-branch (condition is false).

        Returns:
            Deep copy of domain with branch constraint as path constraint.
        """
        if not isinstance(domain, IntervalDomain):
            return domain

        filtered_domain = domain.deep_copy()

        if filtered_domain.state is None:
            return filtered_domain

        condition_name = get_variable_name(condition.value)
        comparison_info = filtered_domain.state.get_comparison(condition_name)

        if comparison_info is None:
            logger.debug(
                "No comparison info for condition variable {name}",
                name=condition_name,
            )
            return filtered_domain

        branch_constraint = self._create_branch_constraint(
            comparison_info.condition, branch_taken
        )
        filtered_domain.state.add_path_constraint(branch_constraint)
        return filtered_domain

    def _create_branch_constraint(
        self, condition_term: "SMTTerm", branch_taken: bool
    ) -> "SMTTerm":
        """Create the path constraint for a branch."""
        if branch_taken:
            return condition_term
        return self._solver.Not(condition_term)
