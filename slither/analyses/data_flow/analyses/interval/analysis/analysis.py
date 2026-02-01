"""Interval analysis implementation."""

from __future__ import annotations

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.smt_solver.solver import SMTSolver
from slither.core.cfg.node import Node
from slither.slithir.operations.operation import Operation


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
            self._initialize_domain_from_bottom(node, domain)
            self._dispatch_operation(operation, domain, node)
            return

        self._dispatch_operation(operation, domain, node)

    def _initialize_domain_from_bottom(
        self,
        node: Node,
        domain: IntervalDomain,
    ) -> None:
        """Initialize domain state from bottom."""
        domain.variant = DomainVariant.STATE
        domain.state = State({})

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
