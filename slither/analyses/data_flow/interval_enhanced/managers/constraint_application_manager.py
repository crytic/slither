from decimal import Decimal
from typing import List

from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.managers.arithmetic_solver_manager import (
    ArithmeticSolverManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.constraint_range_manager import (
    ConstraintRangeManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.operand_analysis_manager import (
    OperandAnalysisManager,
)
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant


class ConstraintApplicationManager:
    """Handles constraint application logic for interval analysis."""

    def __init__(
        self,
        operand_analyzer: OperandAnalysisManager,
        constraint_range_manager: ConstraintRangeManager,
        arithmetic_solver: ArithmeticSolverManager,
        variable_manager: VariableManager,
    ):
        self.operand_analyzer = operand_analyzer
        self.constraint_range_manager = constraint_range_manager
        self.arithmetic_solver = arithmetic_solver
        self.variable_manager = variable_manager

    def apply_constraint_from_binary_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from a binary condition"""
        if condition.type in [
            BinaryType.GREATER,
            BinaryType.LESS,
            BinaryType.GREATER_EQUAL,
            BinaryType.LESS_EQUAL,
            BinaryType.EQUAL,
            BinaryType.NOT_EQUAL,
        ]:
            self.apply_constraint_from_comparison_condition(condition, domain)
        else:
            logger.error(f"Unknown comparison operator for binary condition: {condition.type}")
            raise ValueError(f"Unknown comparison operator for binary condition: {condition.type}")

    def apply_constraint_from_comparison_condition(
        self, condition: Binary, domain: IntervalDomain
    ) -> None:
        """Apply constraint from comparison condition by refining variable bounds"""

        # Get the left and right operands
        left_operand = condition.variable_left
        right_operand = condition.variable_right

        left_is_variable = not self.operand_analyzer.is_operand_constant(left_operand, domain)
        right_is_variable = not self.operand_analyzer.is_operand_constant(right_operand, domain)

        if left_is_variable and not right_is_variable:
            # Case 1: variable op constant
            if not isinstance(left_operand, Variable):
                logger.error(f"Left operand is not a variable: {left_operand}")
                raise ValueError(f"Left operand is not a variable: {left_operand}")

            if not isinstance(right_operand, Constant):
                logger.error(f"Right operand is not a constant: {right_operand}")
                raise ValueError(f"Right operand is not a constant: {right_operand}")

            right_operand_value = right_operand.value

            if not isinstance(right_operand_value, int):
                logger.error(f"Right operand value is not an integer: {right_operand_value}")
                raise ValueError(f"Right operand value is not an integer: {right_operand_value}")

            self.update_variable_bounds_from_condition(
                left_operand, Decimal(right_operand_value), condition.type, domain
            )

        elif right_is_variable and not left_is_variable:
            # Case 2: constant op variable
            if not isinstance(right_operand, Variable):
                logger.error(f"Right operand is not a variable: {right_operand}")
                raise ValueError(f"Right operand is not a variable: {right_operand}")

            if not isinstance(left_operand, Constant):
                logger.error(f"Left operand is not a constant: {left_operand}")
                raise ValueError(f"Left operand is not a constant: {left_operand}")

            left_operand_value = left_operand.value

            if not isinstance(left_operand_value, int):
                logger.error(f"Left operand value is not an integer: {left_operand_value}")
                raise ValueError(f"Left operand value is not an integer: {left_operand_value}")

            # For constant op variable, we need to flip the operator
            flipped_op_type = self.constraint_range_manager.flip_comparison_operator(condition.type)
            self.update_variable_bounds_from_condition(
                right_operand, Decimal(left_operand_value), flipped_op_type, domain
            )

        elif left_is_variable and right_is_variable:
            # Case 3: variable op variable
            if not isinstance(left_operand, Variable):
                logger.error(f"Left operand is not a variable: {left_operand}")
                raise ValueError(f"Left operand is not a variable: {left_operand}")

            if not isinstance(right_operand, Variable):
                logger.error(f"Right operand is not a variable: {right_operand}")
                raise ValueError(f"Right operand is not a variable: {right_operand}")

            self.update_variable_bounds_from_variable_comparison(
                left_operand, right_operand, condition.type, domain
            )

        else:
            # Case 4: constant op constant
            logger.debug(f"Constant comparison: {left_operand} {condition.type} {right_operand}")

    def update_variable_bounds_from_condition(
        self, variable: Variable, value: Decimal, op_type: BinaryType, domain: IntervalDomain
    ) -> None:
        """Update variable bounds from a condition"""
        # Get variable name and retrieve current state
        variable_name = self.variable_manager.get_variable_name(variable)

        # Handle case where variable doesn't exist in domain
        if variable_name not in domain.state.info:
            logger.error(f"Variable '{variable_name}' not found in domain state")
            raise ValueError(f"Variable '{variable_name}' not found in domain state")

        state_info = domain.state.info[variable_name]

        if op_type == BinaryType.EQUAL:
            # Clear the intervals and set the exact value as valid
            state_info.clear_intervals()
            state_info.valid_values.add(value)  # Add the exact value
            return

        if op_type == BinaryType.NOT_EQUAL:
            # Add the excluded value to invalid_values
            state_info.invalid_values.add(value)
            return

        # Get type bounds for the variable
        type_min, type_max = state_info.get_type_bounds()

        # Create constraint range based on comparison operator
        constraint_range = self.constraint_range_manager.create_constraint_range(
            value, op_type, type_min, type_max
        )

        # Apply constraint to all existing intervals
        constrained_ranges = []
        for existing_range in state_info.interval_ranges:
            intersection = existing_range.intersection(constraint_range)
            if intersection is not None:
                constrained_ranges.append(intersection)

        # Update the variable's interval ranges
        state_info.interval_ranges = constrained_ranges

    def update_variable_bounds_from_variable_comparison(
        self, left_var: Variable, right_var: Variable, op_type: BinaryType, domain: IntervalDomain
    ) -> None:
        """Update variable bounds from variable-to-variable comparison"""
        left_var_name = self.variable_manager.get_variable_name(left_var)
        right_var_name = self.variable_manager.get_variable_name(right_var)

        left_state = domain.state.info[left_var_name]
        right_state = domain.state.info[right_var_name]

        left_type_min, left_type_max = left_state.get_type_bounds()
        right_type_min, right_type_max = right_state.get_type_bounds()

        # Apply constraints based on operator
        if op_type == BinaryType.LESS:
            # left <= right - 1, right >= left + 1
            left_constraint = self.constraint_range_manager.create_constraint_range(
                value=right_type_max - Decimal("1"),
                op_type=BinaryType.LESS_EQUAL,
                type_min=left_type_min,
                type_max=left_type_max,
            )
            right_constraint = self.constraint_range_manager.create_constraint_range(
                value=left_type_min + Decimal("1"),
                op_type=BinaryType.GREATER_EQUAL,
                type_min=right_type_min,
                type_max=right_type_max,
            )

        elif op_type == BinaryType.LESS_EQUAL:
            # left <= right, right >= left
            left_constraint = self.constraint_range_manager.create_constraint_range(
                value=right_type_max,
                op_type=BinaryType.LESS_EQUAL,
                type_min=left_type_min,
                type_max=left_type_max,
            )
            right_constraint = self.constraint_range_manager.create_constraint_range(
                value=left_type_min,
                op_type=BinaryType.GREATER_EQUAL,
                type_min=right_type_min,
                type_max=right_type_max,
            )

        elif op_type == BinaryType.GREATER:
            # left >= right + 1, right <= left - 1
            left_constraint = self.constraint_range_manager.create_constraint_range(
                value=right_type_min + Decimal("1"),
                op_type=BinaryType.GREATER_EQUAL,
                type_min=left_type_min,
                type_max=left_type_max,
            )
            right_constraint = self.constraint_range_manager.create_constraint_range(
                value=left_type_max - Decimal("1"),
                op_type=BinaryType.LESS_EQUAL,
                type_min=right_type_min,
                type_max=right_type_max,
            )

        elif op_type == BinaryType.GREATER_EQUAL:
            # left >= right, right <= left
            left_constraint = self.constraint_range_manager.create_constraint_range(
                value=right_type_min + Decimal("1"),
                op_type=BinaryType.GREATER_EQUAL,
                type_min=left_type_min,
                type_max=left_type_max,
            )
            right_constraint = self.constraint_range_manager.create_constraint_range(
                value=left_type_max - Decimal("1"),
                op_type=BinaryType.LESS_EQUAL,
                type_min=right_type_min,
                type_max=right_type_max,
            )

        elif op_type == BinaryType.EQUAL:
            # left == right, both variables must have the same value
            left_valid_values = left_state.valid_values.deep_copy()
            right_valid_values = right_state.valid_values.deep_copy()

            # Get intersection of valid values from both variables
            intersection_values = left_valid_values.intersection(right_valid_values)

            # If both have valid values, use their intersection
            if not left_valid_values.is_empty() and not right_valid_values.is_empty():
                # Both variables have specific valid values - use intersection
                left_state.clear_intervals()
                right_state.clear_intervals()
                left_state.valid_values = intersection_values
                right_state.valid_values = intersection_values.deep_copy()
            else:
                left_constraint = IntervalRange(
                    lower_bound=left_type_min, upper_bound=left_type_max
                )
                right_constraint = IntervalRange(
                    lower_bound=right_type_min, upper_bound=right_type_max
                )

                # Apply constraints to both variables
                self.constraint_range_manager.apply_constraint_to_variable(
                    left_var_name, left_constraint, domain
                )
                self.constraint_range_manager.apply_constraint_to_variable(
                    right_var_name, right_constraint, domain
                )

            logger.debug(f"Applied equality constraint: {left_var_name} == {right_var_name}")
            return  # Early return since we handled this case specially

        elif op_type == BinaryType.NOT_EQUAL:
            # left != right
            left_constraint = IntervalRange(lower_bound=left_type_min, upper_bound=left_type_max)
            right_constraint = IntervalRange(lower_bound=right_type_min, upper_bound=right_type_max)

        else:
            logger.warning(f"Unknown comparison operator for variable comparison: {op_type}")
            return

        # Apply constraints to both variables
        self.constraint_range_manager.apply_constraint_to_variable(
            left_var_name, left_constraint, domain
        )
        self.constraint_range_manager.apply_constraint_to_variable(
            right_var_name, right_constraint, domain
        )

        logger.debug(
            f"Applied variable comparison constraint: {left_var_name} {op_type} {right_var_name}"
        )

    def merge_constraints_from_callee(
        self, arg_name: str, param_state_info: StateInfo, domain: IntervalDomain
    ) -> None:
        """Merge constraints from callee parameter back to caller argument."""
        current_state_info = domain.state.info[arg_name]

        # If parameter has valid values, prioritize them
        if not param_state_info.valid_values.is_empty():
            # Use parameter's valid values and clear intervals
            merged_state_info = StateInfo(
                interval_ranges=[],  # Clear intervals when we have valid values
                valid_values=param_state_info.valid_values.deep_copy(),
                invalid_values=param_state_info.invalid_values.deep_copy(),
                var_type=current_state_info.var_type,
            )
        else:
            # Merge interval ranges through intersection
            merged_ranges = []
            for current_range in current_state_info.interval_ranges:
                for param_range in param_state_info.interval_ranges:
                    intersection = current_range.intersection(param_range)
                    if intersection is not None:
                        merged_ranges.append(intersection)

            # Merge valid values through intersection
            merged_valid = current_state_info.valid_values.intersection(
                param_state_info.valid_values
            )

            # Merge invalid values through union
            merged_invalid = current_state_info.invalid_values.join(param_state_info.invalid_values)

            # Create merged state info
            merged_state_info = StateInfo(
                interval_ranges=merged_ranges,
                valid_values=merged_valid,
                invalid_values=merged_invalid,
                var_type=current_state_info.var_type,
            )

        domain.state.info[arg_name] = merged_state_info

    def merge_constraints_from_caller(
        self, param_name: str, arg_state_info: StateInfo, domain: IntervalDomain
    ) -> None:
        """Merge constraints from caller argument to callee parameter."""
        current_state_info = domain.state.info[param_name]

        # If argument has valid values, prioritize them
        if not arg_state_info.valid_values.is_empty():

            # Use argument's valid values and clear intervals
            merged_state_info = StateInfo(
                interval_ranges=[],  # Clear intervals when we have valid values
                valid_values=arg_state_info.valid_values.deep_copy(),
                invalid_values=arg_state_info.invalid_values.deep_copy(),
                var_type=current_state_info.var_type,
            )
        else:
            # Merge interval ranges through intersection
            merged_ranges = []
            for current_range in current_state_info.interval_ranges:
                for arg_range in arg_state_info.interval_ranges:
                    intersection = current_range.intersection(arg_range)
                    if intersection is not None:
                        merged_ranges.append(intersection)

            # Merge valid values through intersection
            merged_valid = current_state_info.valid_values.intersection(arg_state_info.valid_values)

            # Merge invalid values through union
            merged_invalid = current_state_info.invalid_values.join(arg_state_info.invalid_values)

            # Create merged state info
            merged_state_info = StateInfo(
                interval_ranges=merged_ranges,
                valid_values=merged_valid,
                invalid_values=merged_invalid,
                var_type=current_state_info.var_type,
            )

        domain.state.info[param_name] = merged_state_info

    def create_constant_constraint(
        self, var_name: str, constant: Constant, var_type: ElementaryType, domain: IntervalDomain
    ) -> None:
        """Create a constant constraint for a variable."""
        const_value = Decimal(str(constant.value))
        state_info = StateInfo(
            [IntervalRange(const_value, const_value)],
            SingleValues(const_value),
            SingleValues(),
            var_type,
        )
        state_info.clear_intervals()
        domain.state.info[var_name] = state_info
