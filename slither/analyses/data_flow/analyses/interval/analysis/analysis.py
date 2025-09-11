from typing import Optional

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.handlers.operation_handler import OperationHandler
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.solidity_call import SolidityCall


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
        self._variable_info_manager = VariableInfoManager()

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

        if self.node_declares_variable_without_initial_value(node):
            self._operation_handler.handle_uninitialized_variable(node, domain)

        if isinstance(operation, Assignment):
            self._operation_handler.handle_assignment(node, domain, operation)

        if isinstance(operation, Binary):
            if operation.type in self.ARITHMETIC_OPERATORS:
                self._operation_handler.handle_arithmetic(node, domain, operation)
            elif operation.type in self.COMPARISON_OPERATORS:
                self._operation_handler.handle_comparison(node, domain, operation)

        if isinstance(operation, SolidityCall):
            self._operation_handler.handle_solidity_call(node, domain, operation)

    def node_declares_variable_without_initial_value(self, node: Node) -> bool:
        """Check if the node has an uninitialized variable."""
        if not hasattr(node, "variable_declaration"):
            return False

        var = node.variable_declaration
        if var is None:
            return False

        # Check if variable has no initial value
        return not hasattr(var, "expression") or var.expression is None

    def _initialize_domain_from_bottom(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom variant with function parameters."""
        domain.variant = DomainVariant.STATE

        # Initialize function parameters
        for parameter in node.function.parameters:
            if isinstance(
                parameter.type, ElementaryType
            ) and self._variable_info_manager.is_type_numeric(parameter.type):
                # Create interval range with type bounds
                interval_range = IntervalRange(
                    lower_bound=parameter.type.min,
                    upper_bound=parameter.type.max,
                )
                # Create range variable for the parameter
                range_variable = RangeVariable(
                    interval_ranges=[interval_range],
                    valid_values=None,
                    invalid_values=None,
                    var_type=parameter.type,
                )
                # Add to domain state
                domain.state.add_range_variable(parameter.canonical_name, range_variable)
            elif hasattr(parameter.type, "type") and hasattr(parameter.type.type, "elems"):
                # Struct types are not implemented yet
                raise NotImplementedError("Struct parameter types are not implemented yet")
