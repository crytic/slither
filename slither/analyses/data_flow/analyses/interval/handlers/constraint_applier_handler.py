from typing import Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import \
    IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.interval_refiner import \
    IntervalRefiner
from slither.analyses.data_flow.analyses.interval.managers.constraint_store_manager import \
    ConstraintStoreManager
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import \
    VariableInfoManager
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant


class ConstraintApplierHandler:
    """Handles applying comparison constraints to the domain."""

    def __init__(self, constraint_store: ConstraintStoreManager):
        self.constraint_store = constraint_store
        self.variable_manager = VariableInfoManager()

    def apply_constraint_from_variable(
        self, condition_variable: Variable, domain: IntervalDomain
    ) -> None:
        """Apply a constraint from a condition variable (used by require/assert functions)."""
        try:
            condition_variable_name = self.variable_manager.get_variable_name(condition_variable)

            # Check if variable exists in domain state
            if not domain.state.has_range_variable(condition_variable_name):
                logger.error(f"Variable '{condition_variable_name}' not found in domain state")
                raise ValueError(f"Variable '{condition_variable_name}' not found in domain state")

            # Check if it was assigned from a temporary variable (bool r=x>50; require(r))
            temp_var_name = domain.state.get_temp_var_for_local(condition_variable_name)

            # If no mapping exists, condition variable is the temporary variable itself (require(x>50))
            if temp_var_name is None:
                temp_var_name = condition_variable_name

            stored_constraint = self.constraint_store.get_variable_constraint(temp_var_name)

            self._apply_comparison_constraint(stored_constraint, domain)

        except Exception as e:
            logger.error(f"Error applying constraint from variable: {e}")
            raise ValueError(f"Error applying constraint from variable: {e}")

    def _apply_comparison_constraint(
        self, comparison_operation: Binary, domain: IntervalDomain
    ) -> None:
        """Apply a comparison constraint to the domain."""
        logger.debug(f"Applying comparison constraint: {comparison_operation.type}")

        # Apply the comparison operation to the domain
        left_operand = comparison_operation.variable_left
        right_operand = comparison_operation.variable_right
        operation_type = comparison_operation.type

        # Apply the constraint to the domain state
        self._apply_comparison_to_domain(left_operand, right_operand, operation_type, domain)

    def _apply_comparison_to_domain(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        operation_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply a comparison constraint to the domain state."""
        try:
            # Determine which operands are variables vs constants
            left_is_variable = self._is_variable(left_operand)
            right_is_variable = self._is_variable(right_operand)

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

    def _is_variable(self, operand: Union[Variable, Constant]) -> bool:
        """Check if operand is a variable (not a constant)."""
        return not isinstance(operand, Constant)

    def _flip_comparison_operator(self, operation_type: BinaryType) -> BinaryType:
        """Flip a comparison operator (e.g., < becomes >)."""
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
        """Apply constraint for variable < constant case."""
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
            IntervalRefiner.refine_variable_range(range_var, constant_value, operation_type)

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
        """Apply constraint for variable < variable case."""
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
