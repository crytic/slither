from typing import Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.handlers.operation_handler import OperationHandler
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.operation import Operation


class IntervalAnalysis(Analysis):
    """Interval analysis for data flow analysis."""

    ARITHMETIC_OPERATORS: set[BinaryType] = {
        BinaryType.ADDITION,
        BinaryType.SUBTRACTION,
        BinaryType.MULTIPLICATION,
        BinaryType.DIVISION,
    }

    # Comparison operators
    COMPARISON_OPERATORS: set[BinaryType] = {
        BinaryType.GREATER,
        BinaryType.LESS,
        BinaryType.GREATER_EQUAL,
        BinaryType.LESS_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
    }

    def __init__(self) -> None:
        self._direction: Direction = Forward()
        self._operation_handler = OperationHandler()

    def domain(self) -> Domain:
        return IntervalDomain.with_state({})

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
            # Initialize domain from bottom
            domain.variant = DomainVariant.STATE
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
        if isinstance(operation, Assignment):
            self._operation_handler.handle_assignment(node, domain, operation)

        if isinstance(operation, Binary):
            if operation.type in self.ARITHMETIC_OPERATORS:
                self._operation_handler.handle_arithmetic(node, domain, operation)
            elif operation.type in self.COMPARISON_OPERATORS:
                self._operation_handler.handle_comparison(node, domain, operation)
