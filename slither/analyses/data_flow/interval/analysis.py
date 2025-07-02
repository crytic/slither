from typing import List, Optional

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.analyses.data_flow.interval.constraint_manager import ConstraintManager
from slither.analyses.data_flow.interval.domain import DomainVariant, IntervalDomain
from slither.analyses.data_flow.interval.function_call_analyzer import FunctionCallAnalyzer
from slither.analyses.data_flow.interval.interval_calculator import IntervalCalculator
from slither.analyses.data_flow.interval.operation_handler import OperationHandler
from slither.analyses.data_flow.interval.state import IntervalState
from slither.analyses.data_flow.interval.type_system import TypeSystem
from slither.analyses.data_flow.interval.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.solidity_call import SolidityCall


class IntervalAnalysis(Analysis):
    """
    Main orchestrator for interval analysis.
    Coordinates all components and manages the analysis flow.
    """

    def __init__(self) -> None:
        self._direction: Direction = Forward()

        # Initialize all component classes
        self._type_system = TypeSystem()
        self._variable_manager = VariableManager(self._type_system)
        self._constraint_manager = ConstraintManager(self._type_system, self._variable_manager)
        self._operation_handler = OperationHandler(
            self._type_system, self._variable_manager, self._constraint_manager
        )
        self._function_call_analyzer = FunctionCallAnalyzer(
            self._type_system, self._variable_manager
        )

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
        domain.state = IntervalState({})

        for parameter in node.function.parameters:
            if isinstance(parameter.type, ElementaryType) and self._type_system.is_numeric_type(
                parameter.type
            ):
                min_val, max_val = self._type_system.get_type_bounds(parameter.type)
                domain.state.info[parameter.canonical_name] = (
                    IntervalCalculator.create_interval_from_type(parameter.type, min_val, max_val)
                )

    def _analyze_operation_by_type(
        self, operation: Operation, domain: IntervalDomain, node: Node, functions: List[Function]
    ) -> None:
        """Route operation to appropriate handler based on type."""
        if isinstance(operation, Binary):
            if operation.type in self._constraint_manager.ARITHMETIC_OPERATORS:
                self._operation_handler.handle_arithmetic_operation(domain, operation, node)
            elif (
                operation.type in self._constraint_manager.COMPARISON_OPERATORS
                or operation.type in self._constraint_manager.LOGICAL_OPERATORS
            ):
                self.handle_comparison_operation(node, domain, operation)
        elif isinstance(operation, Assignment):
            self._operation_handler.handle_assignment(node, domain, operation)
        elif isinstance(operation, SolidityCall):
            self.handle_solidity_call(node, domain, operation)
        elif isinstance(operation, InternalCall):
            self._function_call_analyzer.handle_function_call(
                node, domain, operation, functions, self
            )
        elif isinstance(operation, Return):
            self._operation_handler.handle_return_operation(node, domain, operation)

    def handle_comparison_operation(
        self, node: Node, domain: IntervalDomain, operation: Binary
    ) -> None:
        """Handle comparison operations by storing them as pending constraints."""
        if hasattr(operation, "lvalue") and operation.lvalue:
            var_name: str = self._variable_manager.get_canonical_name(operation.lvalue)
            self._constraint_manager.add_pending_constraint(var_name, operation)

    def handle_solidity_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        require_assert_functions: List[str] = [
            "require(bool)",
            "assert(bool)",
            "require(bool,string)",
            "require(bool,error)",
        ]

        if operation.function.name not in require_assert_functions:
            return

        if operation.arguments and len(operation.arguments) > 0:
            condition = operation.arguments[0]
            self._constraint_manager.apply_constraint_from_condition(condition, domain)
