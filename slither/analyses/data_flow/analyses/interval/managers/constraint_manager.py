from typing import Union, List

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
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
from slither.slithir.variables.constant import Constant
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

    def copy_callee_parameter_constraints_back_to_caller_arguments(
        self,
        caller_arguments: List[Variable],
        callee_parameters: List[LocalVariable],
        domain: IntervalDomain,
    ) -> None:
        """Copy constraints from callee parameters back to caller arguments for interprocedural analysis."""
        for caller_argument, callee_parameter in zip(caller_arguments, callee_parameters):
            # Skip non-numeric parameters as they don't have interval constraints
            if not (
                isinstance(callee_parameter.type, ElementaryType)
                and self.variable_manager.is_type_numeric(callee_parameter.type)
            ):
                continue

            caller_argument_name = self.variable_manager.get_variable_name(caller_argument)
            callee_parameter_name = self.variable_manager.get_variable_name(callee_parameter)

            if not domain.state.has_range_variable(callee_parameter_name):
                continue

            callee_parameter_range_variable = domain.state.get_range_variable(callee_parameter_name)

            domain.state.set_range_variable(
                caller_argument_name, callee_parameter_range_variable.deep_copy()
            )

    def copy_callee_return_constraints_to_caller_variable(
        self,
        caller_return_variable: Variable,
        callee_return_values: List[Variable],
        callee_return_types: List,
        domain: IntervalDomain,
    ) -> None:
        """Copy constraints from callee function return values to caller's return variable."""
        # Early return if no return variable or return types
        if not caller_return_variable or not callee_return_types:
            return

        # Handle single return value
        if len(callee_return_values) == 1 and len(callee_return_types) == 1:
            return_type = callee_return_types[0]
            if isinstance(return_type, ElementaryType) and self.variable_manager.is_type_numeric(
                return_type
            ):
                callee_return_value = callee_return_values[0]
                caller_return_var_name = self.variable_manager.get_variable_name(
                    caller_return_variable
                )

                if isinstance(callee_return_value, Variable):
                    callee_return_value_name = self.variable_manager.get_variable_name(
                        callee_return_value
                    )
                    # Look for the return value identifier created by OperationHandler
                    return_identifier = f"return_{callee_return_value_name}"
                    if domain.state.has_range_variable(return_identifier):
                        callee_return_range = domain.state.get_range_variable(return_identifier)
                        domain.state.set_range_variable(
                            caller_return_var_name, callee_return_range.deep_copy()
                        )
                    elif domain.state.has_range_variable(callee_return_value_name):
                        # Fallback to original variable name
                        callee_return_range = domain.state.get_range_variable(
                            callee_return_value_name
                        )
                        domain.state.set_range_variable(
                            caller_return_var_name, callee_return_range.deep_copy()
                        )
                elif isinstance(callee_return_value, Constant):
                    # Use constraint application manager to create constant value range variable
                    self.constraint_applier.create_constant_value_range_variable(
                        caller_return_var_name, callee_return_value, return_type, domain
                    )

        # Handle multiple return values
        elif len(callee_return_values) > 1 and len(callee_return_types) > 1:
            self._process_multiple_return_values(
                caller_return_variable, callee_return_values, callee_return_types, domain
            )

    def _process_multiple_return_values(
        self,
        caller_return_variable: Variable,
        callee_return_values: List[Variable],
        callee_return_types: List,
        domain: IntervalDomain,
    ) -> None:
        """Process multiple return values and apply constraints."""
        # Early return if no caller return variable
        if not caller_return_variable:
            return

        # Early return if no return types to process
        if not callee_return_types:
            return

        # Process each return value and type pair
        for i, (callee_return_value, callee_return_type) in enumerate(
            zip(callee_return_values, callee_return_types)
        ):
            # Only process numeric types
            if not (
                isinstance(callee_return_type, ElementaryType)
                and self.variable_manager.is_type_numeric(callee_return_type)
            ):
                continue

            # Create a variable name for this return value
            return_var_name = f"return_{i}"

            if isinstance(callee_return_value, Constant):
                # Use constraint application manager to create constant value range variable
                self.constraint_applier.create_constant_value_range_variable(
                    return_var_name, callee_return_value, callee_return_type, domain
                )
            elif isinstance(callee_return_value, Variable):
                # Return value is a variable
                callee_var_name = self.variable_manager.get_variable_name(callee_return_value)
                if domain.state.has_range_variable(callee_var_name):
                    callee_range_variable = domain.state.get_range_variable(callee_var_name)
                    domain.state.set_range_variable(
                        return_var_name, callee_range_variable.deep_copy()
                    )
