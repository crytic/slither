from typing import Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.variables import (
    handle_variable_declaration,
    initialize_global_solidity_variables,
)
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.analyses.interval.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.core.cfg.node import Node
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
        """Initialize domain state from bottom variant with global Solidity variables."""
        domain.variant = DomainVariant.STATE
        initialize_global_solidity_variables(self._solver, domain)

    @property
    def solver(self) -> SMTSolver:
        """Get the SMT solver instance."""
        return self._solver
