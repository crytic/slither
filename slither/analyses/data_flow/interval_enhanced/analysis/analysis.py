from typing import List, Optional

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.analyses.data_flow.interval_enhanced.analysis.domain import (
    DomainVariant, IntervalDomain)
from slither.analyses.data_flow.interval_enhanced.handlers.handle_operation import \
    OperationHandler
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.operation import Operation

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

# Logical operators
LOGICAL_OPERATORS: set[BinaryType] = {
    BinaryType.ANDAND,
    BinaryType.OROR,
}


class IntervalAnalysisEnhanced(Analysis):
    """
    Main orchestrator for interval analysis.
    Coordinates all components and manages the analysis flow.
    """

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
        functions: List[Function],
    ) -> None:
        self.transfer_function_helper(node, domain, operation, functions)

    def transfer_function_helper(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: Operation,
        functions: Optional[List[Function]] = None,
    ) -> None:
        if domain.variant == DomainVariant.TOP:
            return
        elif domain.variant == DomainVariant.BOTTOM:
            domain.variant = DomainVariant.STATE
            self._analyze_operation_by_type(operation, domain, node, functions or [])
        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node, functions or [])

    def _analyze_operation_by_type(
        self, operation: Operation, domain: IntervalDomain, node: Node, functions: List[Function]
    ) -> None:
        """Route operation to appropriate handler based on type."""

        if isinstance(operation, Assignment):
            self._operation_handler.handle_assignment(node, domain, operation)
        if isinstance(operation, Binary):
            if operation.type in ARITHMETIC_OPERATORS:
                self._operation_handler.handle_arithmetic(node, domain, operation)
