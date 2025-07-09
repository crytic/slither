from typing import List, Optional

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.analyses.data_flow.interval_enhanced.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.analyses.data_flow.interval_enhanced.handlers.handle_operation import OperationHandler
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType

from slither.slithir.operations.operation import Operation
from slither.slithir.operations.solidity_call import SolidityCall


class IntervalAnalysisEnhanced(Analysis):
    """
    Main orchestrator for interval analysis.
    Coordinates all components and manages the analysis flow.
    """

    def __init__(self) -> None:
        self._direction: Direction = Forward()
        self._constraint_manager = ConstraintManager()
        self._operation_handler = OperationHandler(self._constraint_manager)

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

            self._initialize_domain_from_bottom(node, domain)

            self._analyze_operation_by_type(operation, domain, node, functions or [])
        elif domain.variant == DomainVariant.STATE:
            self._analyze_operation_by_type(operation, domain, node, functions or [])

    def _initialize_domain_from_bottom(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom variant with function parameters."""
        domain.variant = DomainVariant.STATE

        for parameter in node.function.parameters:
            if isinstance(parameter.type, ElementaryType) and self.is_numeric_type(parameter.type):
                interval_range = IntervalRange(
                    lower_bound=parameter.type.min,
                    upper_bound=parameter.type.max,
                )
                state_info = StateInfo(
                    interval_ranges=[interval_range],
                    valid_values=SingleValues(),
                    invalid_values=SingleValues(),
                    var_type=parameter.type,
                )
                domain.state.info[parameter.canonical_name] = state_info

    def is_numeric_type(self, elementary_type: ElementaryType) -> bool:
        """Check if type is numeric."""
        if not elementary_type:
            return False
        type_name = elementary_type.name
        return (
            type_name.startswith("int")
            or type_name.startswith("uint")
            or type_name.startswith("fixed")
            or type_name.startswith("ufixed")
        )

    def _analyze_operation_by_type(
        self,
        operation: Optional[Operation],
        domain: IntervalDomain,
        node: Node,
        functions: List[Function],
    ) -> None:
        """Route operation to appropriate handler based on type."""

        if self.has_uninitialized_variable(node) and operation is None:
            self._operation_handler.handle_uninitialized_variable(node, domain)

        if isinstance(operation, Assignment):
            self._operation_handler.handle_assignment(node, domain, operation)

        if isinstance(operation, Binary):
            if operation.type in self._constraint_manager.ARITHMETIC_OPERATORS:
                self._operation_handler.handle_arithmetic(node, domain, operation)
            elif (
                operation.type in self._constraint_manager.COMPARISON_OPERATORS
                or operation.type in self._constraint_manager.LOGICAL_OPERATORS
            ):
                self._operation_handler.handle_comparison(node, domain, operation)
        if isinstance(operation, SolidityCall):
            self._operation_handler.handle_solidity_call(node, domain, operation)

    def has_uninitialized_variable(self, node: Node):  # type: ignore

        if not hasattr(node, "variable_declaration"):
            return False

        var = node.variable_declaration
        if var is None:
            return False

        # Check if variable has no initial value
        return not hasattr(var, "expression") or var.expression is None
