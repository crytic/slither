from decimal import Decimal
from typing import Dict, List, Optional, Set

from loguru import logger

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
from slither.analyses.data_flow.interval_enhanced.analysis.widening import Widening
from slither.analyses.data_flow.interval_enhanced.handlers.handle_operation import OperationHandler
from slither.analyses.data_flow.interval_enhanced.managers.condition_validity_checker_manager import (
    ConditionValidityCheckerManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.variables.temporary import TemporaryVariable


class IntervalAnalysisEnhanced(Analysis):
    """
    Main orchestrator for interval analysis.
    Coordinates all components and manages the analysis flow.
    """

    def __init__(self) -> None:
        self._direction: Direction = Forward()
        self._constraint_manager = ConstraintManager()
        self._operation_handler = OperationHandler(self._constraint_manager)
        self._variable_manager = VariableManager()
        self._condition_validator = ConditionValidityCheckerManager(
            self._variable_manager, self._constraint_manager.operand_analyzer
        )
        self._widening = Widening()

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

            # # Prevent discrete assignments to widened variables
            # if operation and hasattr(operation, "lvalue"):
            #     var_name = self._variable_manager.get_variable_name(operation.lvalue)
            #     if var_name in domain.state.info:
            #         self._widening.prevent_discrete_assignment(
            #             var_name, domain.state.info[var_name]
            #         )

    def apply_condition(
        self, domain: IntervalDomain, condition: Operation, branch_taken: bool
    ) -> IntervalDomain:
        """Apply branch filtering based on the condition and which branch is taken."""
        if not isinstance(condition, Binary):
            return domain

        # Create a copy of the domain to avoid modifying the original
        filtered_domain = domain.deep_copy()

        if branch_taken:
            return self._apply_true_condition(filtered_domain, condition)
        else:
            return self._apply_false_condition(filtered_domain, condition)

    def _apply_true_condition(self, domain: IntervalDomain, operation: Binary) -> IntervalDomain:
        """Apply the condition when the true branch is taken."""
        print(f"🔄 APPLYING TRUE CONDITION: {operation}")

        # Verify condition validity first
        if not self._condition_validator.verify_condition_validity(operation, domain):
            logger.info(f"⚠️ Pruning invalid true branch: {operation}")
            return IntervalDomain.bottom()  # Return BOTTOM to signal unreachable branch

        # Only apply constraint if condition is valid
        self._constraint_manager.apply_constraint_from_variable(operation.lvalue, domain)

        return domain

    def _apply_false_condition(self, domain: IntervalDomain, operation: Binary) -> IntervalDomain:
        """Apply inverse condition when false branch is taken."""

        # Create a negated operation by creating a new Binary with the negated operator
        if not (operation.type in self._constraint_manager.COMPARISON_OPERATORS):
            logger.warning(f"⚠️ Cannot negate operation: {operation.type}")
            return domain

        # Get the negated operator type (logical complement)
        negation_map = {
            BinaryType.GREATER: BinaryType.LESS_EQUAL,  # !(a > b) = (a <= b)
            BinaryType.GREATER_EQUAL: BinaryType.LESS,  # !(a >= b) = (a < b)
            BinaryType.LESS: BinaryType.GREATER_EQUAL,  # !(a < b) = (a >= b)
            BinaryType.LESS_EQUAL: BinaryType.GREATER,  # !(a <= b) = (a > b)
            BinaryType.EQUAL: BinaryType.NOT_EQUAL,  # !(a == b) = (a != b)
            BinaryType.NOT_EQUAL: BinaryType.EQUAL,  # !(a != b) = (a == b)
        }

        negated_op_type = negation_map.get(operation.type)
        if negated_op_type is None:
            print(f"⚠️ Cannot negate operation: {operation.type}")
            return domain

        # Create the actual negated operation
        negated_lvalue = TemporaryVariable(operation.node)
        negated_lvalue.set_type(operation.lvalue.type)

        negated_operation = Binary(
            result=negated_lvalue,
            left_variable=operation.variable_left,
            right_variable=operation.variable_right,
            operation_type=negated_op_type,
        )
        negated_operation.set_node(operation.node)

        # Verify the negated condition validity
        if not self._condition_validator.verify_condition_validity(negated_operation, domain):
            logger.info(f"⚠️ Pruning invalid false branch: negated {operation}")
            return IntervalDomain.bottom()  # Return BOTTOM to signal unreachable branch

        # Store the negated operation as a constraint for the original variable
        var_name = self._variable_manager.get_variable_name(operation.lvalue)
        self._constraint_manager.add_constraint(var_name, negated_operation)

        # Apply the constraint
        self._constraint_manager.apply_constraint_from_variable(operation.lvalue, domain)

        return domain

    def _initialize_domain_from_bottom(self, node: Node, domain: IntervalDomain) -> None:
        """Initialize domain state from bottom variant with function parameters."""
        domain.variant = DomainVariant.STATE

        for parameter in node.function.parameters:
            if isinstance(
                parameter.type, ElementaryType
            ) and self._variable_manager.is_type_numeric(parameter.type):
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
        if isinstance(operation, InternalCall):
            self._operation_handler.handle_internal_call(node, domain, operation, self)

    def has_uninitialized_variable(self, node: Node):  # type: ignore

        if not hasattr(node, "variable_declaration"):
            return False

        var = node.variable_declaration
        if var is None:
            return False

        # Check if variable has no initial value
        return not hasattr(var, "expression") or var.expression is None

    def apply_widening(
        self, current_state: IntervalDomain, previous_state: IntervalDomain, set_b: set
    ) -> IntervalDomain:
        """Apply widening operations to the current state."""
        return self._widening.apply_widening(current_state, previous_state, set_b)
