from typing import Optional

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.handlers.operation_handler import OperationHandler
from slither.analyses.data_flow.analyses.interval.managers.condition_validity_checker_manager import (
    ConditionValidityChecker,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.operand_analysis_manager import (
    OperandAnalysisManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.analyses.data_flow.analyses.interval.analysis.widening import Widening
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.temporary import TemporaryVariable


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
        self._constraint_manager = ConstraintManager()
        self._operand_analyzer = OperandAnalysisManager()
        self._condition_validity_checker = ConditionValidityChecker(
            self._variable_info_manager, self._operand_analyzer
        )
        self._widening = Widening()

    def domain(self) -> Domain:
        return IntervalDomain.with_state({})

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return IntervalDomain.bottom()

    def is_condition_valid(self, condition: Operation, domain: IntervalDomain) -> bool:
        """Check if a condition can be satisfied given the current domain state."""
        return self._condition_validity_checker.is_condition_valid(condition, domain)

    def apply_condition(
        self, domain: IntervalDomain, condition: Operation, branch_taken: bool
    ) -> IntervalDomain:
        """Apply branch filtering based on the condition and which branch is taken.

        Example: For condition "x > 100" in "if (x > 100) { ... } else { ... }":
        - branch_taken=True: applies constraint x > 100 (then branch)
        - branch_taken=False: applies constraint x <= 100 (else branch)
        """

        if not isinstance(condition, Binary):
            return domain

        # Create a copy of the domain to avoid modifying the original
        filtered_domain = domain.deep_copy()

        if branch_taken:
            return self._apply_then_branch_condition(filtered_domain, condition)
        else:
            return self._apply_else_branch_condition(filtered_domain, condition)

    def _apply_then_branch_condition(
        self, domain: IntervalDomain, operation: Binary
    ) -> IntervalDomain:
        """Apply the condition when the then branch is taken."""
        # Verify condition validity first - if invalid, return TOP (unreachable)
        if not self._condition_validity_checker.is_condition_valid(operation, domain):
            return IntervalDomain.top()

        # Apply constraint if condition is valid
        if operation.lvalue is not None:
            var_name = self._variable_info_manager.get_variable_name(operation.lvalue)
            self._constraint_manager.store_variable_constraint(var_name, operation)
            self._constraint_manager.apply_constraint_from_variable(operation.lvalue, domain)

        return domain

    def _apply_else_branch_condition(
        self, domain: IntervalDomain, operation: Binary
    ) -> IntervalDomain:
        """Apply inverse condition when else branch is taken."""

        # Create a negated operation by creating a new Binary with the negated operator
        if operation.type not in self.COMPARISON_OPERATORS:
            logger.error(f"Cannot negate operation: {operation.type}")
            raise ValueError(f"Cannot negate operation: {operation.type}")

        # Get the negated operator type (logical complement)
        negation_map = {
            BinaryType.GREATER: BinaryType.LESS_EQUAL,  # !(a > b) = (a <= b)
            BinaryType.GREATER_EQUAL: BinaryType.LESS,  # !(a >= b) = (a < b)
            BinaryType.LESS: BinaryType.GREATER_EQUAL,  # !(a < b) = (a >= b)
            BinaryType.LESS_EQUAL: BinaryType.GREATER,  # !(a <= b) = (a > b)
            BinaryType.EQUAL: BinaryType.NOT_EQUAL,  # !(a == b) = (a != b)
            BinaryType.NOT_EQUAL: BinaryType.EQUAL,  # !(a != b) = (a == b)
        }

        negated_operator_type = negation_map.get(operation.type)
        if negated_operator_type is None:
            logger.error(f"Cannot negate operation: {operation.type}")
            raise ValueError(f"Cannot negate operation: {operation.type}")

        # Create the actual negated operation
        negated_result_variable = TemporaryVariable(operation.node)
        negated_result_variable.set_type(operation.lvalue.type)

        negated_comparison = Binary(
            result=negated_result_variable,
            left_variable=operation.variable_left,
            right_variable=operation.variable_right,
            operation_type=negated_operator_type,
        )
        negated_comparison.set_node(operation.node)

        # Verify the negated condition validity first
        if not self._condition_validity_checker.is_condition_valid(negated_comparison, domain):
            return IntervalDomain.top()

        # Store the negated operation as a constraint for the original variable
        if operation.lvalue is not None:
            # Handle assignment-based comparisons (bool result = x > 100; if (result))
            var_name = self._variable_info_manager.get_variable_name(operation.lvalue)
            self._constraint_manager.store_variable_constraint(var_name, negated_comparison)
            self._constraint_manager.apply_constraint_from_variable(operation.lvalue, domain)
        else:
            # Handle direct comparisons (if (x > 100)) - store constraint for the actual variable
            if operation.variable_left is not None:
                left_operand_name = self._variable_info_manager.get_variable_name(
                    operation.variable_left
                )
                self._constraint_manager.store_variable_constraint(
                    left_operand_name, negated_comparison
                )
                self._constraint_manager.apply_constraint_from_variable(
                    operation.variable_left, domain
                )

        return domain

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

        if isinstance(operation, InternalCall):
            self._operation_handler.handle_internal_call(node, domain, operation, self)

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

    def apply_widening(
        self, current_state: IntervalDomain, previous_state: IntervalDomain, widening_literals: set
    ) -> IntervalDomain:
        """Apply widening operations to the current state."""
        return self._widening.apply_widening(current_state, previous_state, widening_literals)
