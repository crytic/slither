"""
Constraint storage and retrieval manager.

This module manages the storage and retrieval of constraints per variable,
providing a registry-style interface for constraint management.
"""

from typing import Dict, Optional, Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import \
    VariableInfoManager
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary


class ConstraintStoreManager:
    """Manages storage and retrieval of constraints per variable."""

    def __init__(self):
        # Store constraints from comparison operations for each variable
        self._comparison_constraints: Dict[str, Union[Binary, Variable]] = {}
        # Initialize variable info manager for basic operations
        self.variable_manager = VariableInfoManager()

    def store_variable_constraint(self, var_name: str, constraint: Union[Binary, Variable]) -> None:
        """Store a constraint that applies to a specific variable."""
        self._comparison_constraints[var_name] = constraint
#        logger.debug(f"Stored constraint for variable '{var_name}': {constraint}")

    def get_variable_constraint(self, var_name: str) -> Optional[Union[Binary, Variable]]:
        """Retrieve the constraint stored for a specific variable."""
        return self._comparison_constraints.get(var_name)

    def has_variable_constraint(self, var_name: str) -> bool:
        """Check if a variable has any stored constraints from comparison operations."""
        return var_name in self._comparison_constraints

    def clear_all_constraints(self) -> None:
        """Clear all stored comparison constraints."""
        self._comparison_constraints.clear()
#        logger.debug("Cleared all comparison constraints")

    def get_total_constraint_count(self) -> int:
        """Get the total number of stored constraints."""
        return len(self._comparison_constraints)

    def store_comparison_operation_constraint(self, comparison_operation: Binary) -> None:
        """Store a constraint from a comparison operation (>, <, >=, <=, ==, !=)."""
        try:
            # Get the temporary variable name that contains the comparison
            temp_var_name = self.variable_manager.get_variable_name(comparison_operation.lvalue)

            self.store_variable_constraint(temp_var_name, comparison_operation)

        except Exception as e:
            logger.error(f"Error storing comparison operation constraint: {e}")
            raise
