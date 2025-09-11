from decimal import Decimal
from typing import Dict, List, Optional, Union

from loguru import logger


from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant


class ComparisonConstraintStorage:
    """Stores constraints from comparison operations for future use."""

    def __init__(self):
        # Store constraints from comparison operations for each variable
        self._comparison_constraints: Dict[str, Union[Binary, Variable]] = {}
        # Initialize variable info manager for basic operations
        self.variable_manager = VariableInfoManager()

    # Basic constraint storage methods
    def store_variable_constraint(self, var_name: str, constraint: Union[Binary, Variable]) -> None:
        """Store a constraint that applies to a specific variable"""
        self._comparison_constraints[var_name] = constraint
        logger.debug(f"Stored constraint for variable '{var_name}': {constraint}")

    def get_variable_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Retrieve the constraint stored for a specific variable"""
        return self._comparison_constraints.get(var_name)

    def has_variable_constraint(self, var_name: str) -> bool:
        """Check if a variable has any stored constraints from comparison operations"""
        return var_name in self._comparison_constraints

    def clear_all_constraints(self) -> None:
        """Clear all stored comparison constraints"""
        self._comparison_constraints.clear()
        logger.debug("Cleared all comparison constraints")

    def get_total_constraint_count(self) -> int:
        """Get the total number of stored constraints"""
        return len(self._comparison_constraints)

    # Method for handling comparison operation constraints
    def store_comparison_operation_constraint(
        self, comparison_operation: Binary, domain: IntervalDomain
    ) -> None:
        """Store a constraint from a comparison operation (>, <, >=, <=, ==, !=)"""
        try:
            # Get the temporary variable name that contains the comparison
            temp_var_name = self.variable_manager.get_variable_name(comparison_operation.lvalue)

            self.store_variable_constraint(temp_var_name, comparison_operation)

        except Exception as e:
            logger.error(f"Error storing comparison operation constraint: {e}")
            raise

    def apply_constraint_from_variable(
        self, condition_variable: Variable, domain: IntervalDomain
    ) -> None:
        """Apply a constraint from a condition variable (used by require/assert functions)"""
        try:
            var_name = self.variable_manager.get_variable_name(condition_variable)

            # Check if we have a stored constraint for this variable
            if not self.has_variable_constraint(var_name):
                logger.error(f"No stored constraint found for variable '{var_name}'")
                raise ValueError(f"No stored constraint found for variable '{var_name}'")

            # Get the stored comparison operation
            stored_constraint = self.get_variable_constraint(var_name)

            # The stored constraint should be a Binary operation (comparison)
            if isinstance(stored_constraint, Binary):
                # Extract the actual comparison operation from the stored constraint
                comparison_operation = stored_constraint
                logger.debug(f"Applying comparison operation: {comparison_operation.type}")

                # Apply the comparison operation to the domain
                left_operand = comparison_operation.variable_left
                right_operand = comparison_operation.variable_right
                operation_type = comparison_operation.type

                # Apply the constraint to the domain state
                self._apply_comparison_to_domain(
                    left_operand, right_operand, operation_type, domain
                )
            else:
                logger.error(
                    f"Stored constraint is not a Binary operation: {type(stored_constraint)}"
                )
                raise ValueError(
                    f"Stored constraint is not a Binary operation: {type(stored_constraint)}"
                )

        except Exception as e:
            logger.error(f"Error applying constraint from variable: {e}")
            raise ValueError(f"Error applying constraint from variable: {e}")

    def _apply_comparison_to_domain(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply a comparison constraint to the domain state"""
        try:
            # Determine which operands are variables vs constants
            left_is_variable = self._is_variable_operand(left_operand)
            right_is_variable = self._is_variable_operand(right_operand)

            # Define the four possible comparison scenarios
            variable_compared_to_constant = left_is_variable and not right_is_variable
            constant_compared_to_variable = right_is_variable and not left_is_variable
            variable_compared_to_variable = left_is_variable and right_is_variable
            constant_compared_to_constant = not left_is_variable and not right_is_variable

            if variable_compared_to_constant:
                # Case: variable op constant (e.g., x < 10, x > 5, x == 7)
                self._apply_variable_constant_constraint(
                    left_operand, right_operand, operation_type, domain
                )

            elif constant_compared_to_variable:
                # Case: constant op variable (e.g., 5 < x, 10 > x) - flip the operation
                flipped_operation = self._flip_comparison_operator(operation_type)
                self._apply_variable_constant_constraint(
                    right_operand, left_operand, flipped_operation, domain
                )

            elif variable_compared_to_variable:
                # Case: variable op variable (e.g., x < y, x > z)
                self._apply_variable_variable_constraint(
                    left_operand, right_operand, operation_type, domain
                )

            elif constant_compared_to_constant:
                # Case: constant op constant - no variables to constrain
                logger.debug(
                    f"Constant comparison: {left_operand} {operation_type} {right_operand}"
                )

        except Exception as e:
            logger.error(f"Error applying comparison to domain: {e}")
            raise

    def _is_variable_operand(self, operand: Union[Variable, Constant]) -> bool:
        """Check if operand is a variable (not a constant)"""
        is_variable = not isinstance(operand, Constant)
        return is_variable

    def _flip_comparison_operator(self, operation_type: BinaryType) -> BinaryType:
        """Flip a comparison operator (e.g., < becomes >)"""
        flip_map = {
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL: BinaryType.EQUAL,  # Equal stays the same
            BinaryType.NOT_EQUAL: BinaryType.NOT_EQUAL,  # Not equal stays the same
        }
        return flip_map.get(operation_type, operation_type)

    def _apply_variable_constant_constraint(
        self,
        variable_operand: Variable,
        constant_operand: Constant,
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply constraint for variable < constant case"""
        try:
            var_name = self.variable_manager.get_variable_name(variable_operand)
            range_var = domain.state.get_range_variable(var_name)

            if range_var is None:
                logger.debug(f"No range variable found for '{var_name}' - skipping constraint")
                return

            # Extract constant value
            if hasattr(constant_operand, "value"):
                constant_value = constant_operand.value
            else:
                logger.debug(f"Could not extract constant value from {constant_operand}")
                return

            # Apply the constraint by modifying the range variable's intervals
            self._refine_variable_range(range_var, constant_value, operation_type)

        except Exception as e:
            logger.error(f"Error applying variable-constant constraint: {e}")
            raise

    def _apply_variable_variable_constraint(
        self,
        left_variable: Variable,
        right_variable: Variable,
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply constraint for variable < variable case"""
        try:
            left_var_name = self.variable_manager.get_variable_name(left_variable)
            right_var_name = self.variable_manager.get_variable_name(right_variable)

            left_range_var = domain.state.get_range_variable(left_var_name)
            right_range_var = domain.state.get_range_variable(right_var_name)

            if left_range_var is None or right_range_var is None:
                logger.debug(
                    f"Missing range variables for variable-variable constraint: {left_var_name} {operation_type} {right_var_name}"
                )
                return

            # For now, just log - variable-variable constraints are more complex
            # and would require intersection of ranges
            logger.debug(f"Variable-variable constraint application - implementation needed")

        except Exception as e:
            logger.error(f"Error applying variable-variable constraint: {e}")
            raise

    def _refine_variable_range(
        self,
        range_var: RangeVariable,
        constant_value: Union[int, float, str],
        operation_type: BinaryType,
    ) -> None:
        """Refine a variable's range based on a constant comparison"""
        try:

            constant_decimal = Decimal(str(constant_value))

            # Get the current intervals using the getter method
            current_intervals = range_var.get_interval_ranges()

            if not current_intervals:
                logger.debug("No current intervals to refine")
                return

            # Handle equality constraint specially - use valid_values instead of intervals
            if operation_type == BinaryType.EQUAL:
                # Check if the constant is within any of the current intervals
                constant_in_range = any(
                    interval.get_lower() <= constant_decimal <= interval.get_upper()
                    for interval in current_intervals
                )

                if constant_in_range:
                    # Clear all intervals and add the exact value to valid_values
                    range_var.clear_intervals()
                    range_var.add_valid_value(constant_decimal)
                    logger.debug(
                        f"Set exact value {constant_decimal} in valid_values for equality constraint"
                    )
                else:
                    # Constant is not in any valid range, clear everything
                    range_var.clear_intervals()
                    logger.debug("Constant not in valid range for equality constraint")
                return

            # Handle NOT_EQUAL constraint specially - add constant to invalid_values
            if operation_type == BinaryType.NOT_EQUAL:
                # Add the constant to invalid_values since it's explicitly excluded
                range_var.add_invalid_value(constant_decimal)

            # Create new refined intervals based on the comparison
            new_intervals = []

            for interval in current_intervals:
                refined_interval = self._refine_interval_with_constraint(
                    interval, constant_decimal, operation_type
                )
                if refined_interval is not None:
                    if isinstance(refined_interval, list):
                        # Handle case where interval was split (e.g., for != operator)
                        new_intervals.extend(refined_interval)
                    else:
                        new_intervals.append(refined_interval)

            # Update the range variable with refined intervals using proper methods
            if new_intervals:
                # Clear existing intervals and add new ones
                range_var.clear_intervals()
                for interval in new_intervals:
                    range_var.add_interval_range(interval)

            else:
                # Clear all intervals if no valid ones remain
                range_var.clear_intervals()
                logger.debug("No valid intervals remain after constraint application")

        except Exception as e:
            logger.error(f"Error refining variable range: {e}")
            raise

    def _refine_interval_with_constraint(
        self, interval: IntervalRange, constant_value: Decimal, operation_type: BinaryType
    ) -> Optional[Union[IntervalRange, List[IntervalRange]]]:
        """Refine a single interval based on a constant constraint"""
        try:
            from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
                IntervalRange,
            )

            lower = interval.get_lower()
            upper = interval.get_upper()

            if operation_type == BinaryType.LESS:
                # x < constant: refine upper bound
                if upper > constant_value:
                    new_upper = constant_value - 1  # One less than constant (integer)
                    if new_upper >= lower:
                        return IntervalRange(lower, new_upper)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.LESS_EQUAL:
                # x <= constant: refine upper bound
                if upper > constant_value:
                    if constant_value >= lower:
                        return IntervalRange(lower, constant_value)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.GREATER:
                # x > constant: refine lower bound
                if lower < constant_value:
                    new_lower = constant_value + 1  # One more than constant (integer)
                    if new_lower <= upper:
                        return IntervalRange(new_lower, upper)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.GREATER_EQUAL:
                # x >= constant: refine lower bound
                if lower < constant_value:
                    if constant_value <= upper:
                        return IntervalRange(constant_value, upper)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.EQUAL:
                # x == constant: this should be handled in the main flow, not here
                # Return None to indicate no interval processing needed
                return None

            elif operation_type == BinaryType.NOT_EQUAL:
                # x != constant: split interval if constant is inside
                if lower < constant_value < upper:
                    # Split into two intervals
                    return [
                        IntervalRange(lower, constant_value - 1),
                        IntervalRange(constant_value + 1, upper),
                    ]
                elif constant_value == lower:
                    # Remove lower bound
                    return IntervalRange(constant_value + 1, upper)
                elif constant_value == upper:
                    # Remove upper bound
                    return IntervalRange(lower, constant_value - 1)
                else:
                    # Constant outside interval, no change needed
                    return interval

            # If no constraint applied, return original interval
            return interval

        except Exception as e:
            logger.error(f"Error refining interval: {e}")
            raise
