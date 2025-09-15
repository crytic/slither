from typing import Union, List

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.handlers.constraint_applier_handler import (
    ConstraintApplierHandler,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_store_manager import (
    ConstraintStoreManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.variables.variable import Variable
from slither.core.variables.local_variable import LocalVariable
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary
from loguru import logger


class ConstraintManager:
    """
    Constraint management using modular architecture.
    """

    def __init__(self):
        # Initialize the three specialized components
        self.constraint_store = ConstraintStoreManager()
        self.constraint_applier = ConstraintApplierHandler(self.constraint_store)
        self.variable_manager = VariableInfoManager()

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

    def copy_caller_constraints_to_callee_parameters(
        self,
        caller_arguments: List[Variable],
        callee_parameters: List[LocalVariable],
        domain: IntervalDomain,
    ) -> None:
        """Copy constraints from caller arguments to callee parameters for interprocedural analysis."""
        for caller_arg, callee_param in zip(caller_arguments, callee_parameters):
            # Skip non-numeric parameters as they don't have interval constraints
            if not (
                isinstance(callee_param.type, ElementaryType)
                and self.variable_manager.is_type_numeric(callee_param.type)
            ):
                logger.debug(
                    f"Skipping non-numeric parameter: {callee_param.name} of type {callee_param.type}"
                )
                continue

            caller_arg_name = self.variable_manager.get_variable_name(caller_arg)
            callee_param_name = self.variable_manager.get_variable_name(callee_param)

            # Ensure the caller argument exists in the domain state
            if not domain.state.has_range_variable(caller_arg_name):
                logger.error(
                    f"Caller argument '{caller_arg_name}' not found in domain state during interprocedural analysis"
                )
                raise ValueError(
                    f"Caller argument '{caller_arg_name}' not found in domain state during interprocedural analysis"
                )

            caller_arg_range_variable = domain.state.get_range_variable(caller_arg_name)

            # Copy caller argument constraints to callee parameter
            domain.state.set_range_variable(
                callee_param_name, caller_arg_range_variable.deep_copy()
            )
