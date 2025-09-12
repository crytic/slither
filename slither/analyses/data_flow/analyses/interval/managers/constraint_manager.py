from typing import Union

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.handlers.constraint_applier_handler import (
    ConstraintApplierHandler,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_store_manager import (
    ConstraintStoreManager,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary


class ConstraintManager:
    """
    Constraint management using modular architecture.
    """

    def __init__(self):
        # Initialize the three specialized components
        self.constraint_store = ConstraintStoreManager()
        self.constraint_applier = ConstraintApplierHandler(self.constraint_store)

    # Delegate storage methods to ConstraintStoreManager
    def store_variable_constraint(self, var_name: str, constraint: Union[Binary, Variable]) -> None:
        """Store a constraint that applies to a specific variable."""
        self.constraint_store.store_variable_constraint(var_name, constraint)

    def get_variable_constraint(self, var_name: str):
        """Retrieve the constraint stored for a specific variable."""
        return self.constraint_store.get_variable_constraint(var_name)

    def has_variable_constraint(self, var_name: str) -> bool:
        """Check if a variable has any stored constraints from comparison operations."""
        return self.constraint_store.has_variable_constraint(var_name)

    def clear_all_constraints(self) -> None:
        """Clear all stored comparison constraints."""
        self.constraint_store.clear_all_constraints()

    def get_total_constraint_count(self) -> int:
        """Get the total number of stored constraints."""
        return self.constraint_store.get_total_constraint_count()

    def store_comparison_operation_constraint(
        self, comparison_operation: Binary, domain: IntervalDomain
    ) -> None:
        """Store a constraint from a comparison operation (>, <, >=, <=, ==, !=)."""
        self.constraint_store.store_comparison_operation_constraint(comparison_operation)

    def apply_constraint_from_variable(
        self, condition_variable: Variable, domain: IntervalDomain
    ) -> None:
        """Apply a constraint from a condition variable (used by require/assert functions)."""
        self.constraint_applier.apply_constraint_from_variable(condition_variable, domain)
