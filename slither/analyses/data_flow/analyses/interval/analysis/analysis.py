from typing import List, Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.variables import (
    handle_variable_declaration,
    initialize_fixed_length_arrays,
    initialize_global_solidity_variables,
    initialize_function_parameters,
    initialize_state_variables_with_constants,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.analyses.interval.operations.binary.comparison import (
    ComparisonBinaryHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.phi import PhiHandler
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    reset_overflow_tracking,
)
from slither.analyses.data_flow.analyses.interval.safety.memory_safety import (
    MemorySafetyContext,
    MemorySafetyViolation,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.analyses.data_flow.logger import get_logger
from slither.core.cfg.node import Node
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.operation import Operation


class IntervalAnalysis(Analysis):
    """Interval analysis for data flow analysis."""

    def __init__(self, solver: SMTSolver) -> None:
        """
        Initialize interval analysis.

        Args:
            solver: The SMT solver instance to use for constraint solving
        """
        self._direction: Direction = Forward()
        self._solver: SMTSolver = solver
        self._registry: OperationHandlerRegistry = OperationHandlerRegistry(self._solver, self)
        # Memory safety tracking context
        self._safety_context: MemorySafetyContext = MemorySafetyContext()
        # Detected safety violations
        self._safety_violations: List[MemorySafetyViolation] = []

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
        operation: Operation,
    ) -> None:
        self.transfer_function_helper(node, domain, operation)

    def transfer_function_helper(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation,
    ) -> None:

        if domain.variant == DomainVariant.TOP:
            return
        elif domain.variant == DomainVariant.BOTTOM:
            # Initialize domain from bottom with function parameters
            self._initialize_domain_from_bottom(node, domain)
            # Reset Phi constraint tracking at start of new analysis
            PhiHandler.reset_applied_constraints()
            # Reset overflow tracking to avoid duplicate constraints
            reset_overflow_tracking()
            self._analyze_operation_by_type(operation, domain, node)
        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node)

    def _analyze_operation_by_type(
        self,
        operation: Optional[Operation],
        domain: IntervalDomain,
        node: Node,
    ) -> None:
        """Route operation to appropriate handler based on type."""
        if operation is None:
            if node.variable_declaration:
                handle_variable_declaration(self._solver, domain, node.variable_declaration)
            return

        handler = self._registry.get_handler(operation, node=node, domain=domain)
        handler.handle(operation, domain, node)

    def _initialize_domain_from_bottom(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom variant with global Solidity variables and function parameters."""
        domain.variant = DomainVariant.STATE
        # Initialize global Solidity variables with full range
        initialize_global_solidity_variables(self._solver, domain)
        # Initialize function parameters with full range
        if node.function:
            initialize_function_parameters(self._solver, domain, node.function)
            # Initialize state variables with constant initial values
            initialize_state_variables_with_constants(self._solver, domain, node.function)
            # Initialize fixed-length array elements to 0
            initialize_fixed_length_arrays(self._solver, domain, node.function)

    @property
    def solver(self) -> SMTSolver:
        """Get the SMT solver instance."""
        return self._solver

    @property
    def safety_context(self) -> MemorySafetyContext:
        """Get the memory safety tracking context."""
        return self._safety_context

    @property
    def safety_violations(self) -> List[MemorySafetyViolation]:
        """Get all detected safety violations."""
        return self._safety_violations

    def add_safety_violation(self, violation: MemorySafetyViolation) -> None:
        """Add a detected safety violation."""
        self._safety_violations.append(violation)

    def clear_safety_violations(self) -> None:
        """Clear all detected safety violations."""
        self._safety_violations.clear()

    def apply_condition(
        self,
        domain: Domain,
        condition: Condition,
        branch_taken: bool,
    ) -> Domain:
        """Apply branch-specific constraints to domain based on condition."""
        logger = get_logger()

        # Guard: only process STATE domains
        if not isinstance(domain, IntervalDomain):
            return domain
        if domain.variant != DomainVariant.STATE:
            return domain

        # Create a fresh branch domain so each branch carries only its own constraints
        filtered_domain = self._clone_branch_domain(domain)

        # Get the condition value (e.g., TMP_0 which holds the comparison result)
        condition_value = condition.value
        condition_name = IntervalSMTUtils.resolve_variable_name(condition_value)
        if condition_name is None:
            logger.debug("Could not resolve condition variable name")
            return filtered_domain

        # Get the tracked variable for the condition
        condition_tracked = IntervalSMTUtils.get_tracked_variable(filtered_domain, condition_name)
        if condition_tracked is None:
            logger.debug(
                "Condition variable '{name}' not found in domain",
                name=condition_name,
            )
            return filtered_domain

        # Try to get the original binary operation that produced the condition
        binary_op = ComparisonBinaryHandler.validate_constraint_from_temp(
            condition_name, filtered_domain
        )

        constraint = None
        if binary_op is not None:
            # Build the comparison constraint from the binary operation
            handler = ComparisonBinaryHandler(self._solver)
            constraint = handler.build_comparison_constraint(
                binary_op, filtered_domain, condition.node, binary_op
            )

        if constraint is not None:
            # For false branch, negate the constraint
            if not branch_taken:
                constraint = self._solver.Not(constraint)

            # Store the constraint in the domain state (not in global solver)
            filtered_domain.state.add_path_constraint(constraint)
            logger.debug(
                "Added path constraint for branch_taken={taken}: {constraint}",
                taken=branch_taken,
                constraint=constraint,
            )
            return filtered_domain

        # No constraint could be built - return domain without path constraint
        return filtered_domain

    def _clone_branch_domain(self, domain: IntervalDomain) -> IntervalDomain:
        """Return a branch-specific clone with cleared path constraints."""
        # Guard: ensure we only clone interval domains
        if not isinstance(domain, IntervalDomain):
            return domain

        branch_domain = domain.deep_copy()
        # Clear existing path constraints so we don't mix true/false branches
        branch_domain.state.path_constraints = []
        return branch_domain
