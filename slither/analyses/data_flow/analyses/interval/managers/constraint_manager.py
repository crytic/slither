from typing import Dict, Optional, Union

from loguru import logger
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary


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
            # Get the left and right operands
            left_operand = comparison_operation.variable_left
            right_operand = comparison_operation.variable_right

            # Store constraint for the left operand if it's a variable
            if hasattr(left_operand, "name") and left_operand.name:
                left_var_name = self.variable_manager.get_variable_name(left_operand)
                self.store_variable_constraint(left_var_name, comparison_operation)
                logger.debug(f"Stored comparison constraint for left operand '{left_var_name}'")

            # Store constraint for the right operand if it's a variable
            if hasattr(right_operand, "name") and right_operand.name:
                right_var_name = self.variable_manager.get_variable_name(right_operand)
                self.store_variable_constraint(right_var_name, comparison_operation)
                logger.debug(f"Stored comparison constraint for right operand '{right_var_name}'")

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
            if self.has_variable_constraint(var_name):
                constraint = self.get_variable_constraint(var_name)
                logger.debug(f"Applying stored constraint for variable '{var_name}': {constraint}")

                # TODO: Apply the constraint to the domain
                # This is where the actual constraint application logic would go
                # For now, just log that we would apply it
                logger.debug(f"Constraint application for '{var_name}' - implementation needed")

            else:
                logger.debug(f"No stored constraint found for variable '{var_name}'")

        except Exception as e:
            logger.error(f"Error applying constraint from variable: {e}")
            raise ValueError(f"Error applying constraint from variable: {e}")
