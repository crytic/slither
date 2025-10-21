from typing import List, Union, Optional, TYPE_CHECKING
import decimal

from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.managers.reference_handler import (
        ReferenceHandler,
    )

from IPython import embed
from loguru import logger

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
from slither.analyses.data_flow.analyses.interval.managers.reference_handler import (
    ReferenceHandler,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary
from slither.slithir.variables.constant import Constant


class ConstraintManager:
    """
    Constraint management using modular architecture.
    """

    def __init__(self, reference_handler: Optional[ReferenceHandler] = None) -> None:
        # Initialize the three specialized components
        self.constraint_store = ConstraintStoreManager()
        self.constraint_applier = ConstraintApplierHandler(self.constraint_store, reference_handler)
        self.variable_manager = VariableInfoManager()

    # Delegate storage methods to ConstraintStoreManager
    def store_variable_constraint(
        self, var_name: str, constraint: Union[Binary, Variable, Operation]
    ) -> None:
        """Store a constraint that applies to a specific variable."""
        self.constraint_store.store_variable_constraint(var_name, constraint)

    def get_variable_constraint(
        self, var_name: str
    ) -> Optional[Union[Binary, Variable, Operation]]:
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
        self, condition_variable: Variable, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Apply a constraint from a condition variable (used by require/assert functions)."""
        self.constraint_applier.apply_constraint_from_variable(
            condition_variable, domain, operation
        )

    def copy_caller_constraints_to_callee_parameters(
        self,
        caller_arguments: List[Variable],
        callee_parameters: List[LocalVariable],
        domain: IntervalDomain,
    ) -> None:
        """Copy constraints from caller arguments to callee parameters for interprocedural analysis."""
        for caller_arg, callee_param in zip(caller_arguments, callee_parameters):
            callee_param_name = self.variable_manager.get_variable_name(callee_param)

            # Handle numeric parameters - copy constraints
            if isinstance(
                callee_param.type, ElementaryType
            ) and self.variable_manager.is_type_numeric(callee_param.type):
                caller_arg_name = self.variable_manager.get_variable_name(caller_arg)

                # Ensure the caller argument exists in the domain state
                if not domain.state.has_range_variable(caller_arg_name):
                    # Try to create a range variable for literals/constants
                    if self._create_range_variable_for_literal(caller_arg, domain):
                        logger.debug(
                            f"Created range variable for literal argument: {caller_arg_name}"
                        )
                    else:
                        logger.error(
                            f"Caller argument '{caller_arg_name}' not found in domain state during interprocedural analysis"
                        )
                        # embed()
                        raise ValueError(
                            f"Caller argument '{caller_arg_name}' not found in domain state during interprocedural analysis"
                        )

                # Copy constraints using the reusable method
                self._copy_constraints_between_variables(caller_arg_name, callee_param_name, domain)
            # Handle non-numeric parameters - create placeholder range variables
            elif isinstance(callee_param.type, ElementaryType) and callee_param.type.name in [
                "address",
                "bool",
                "string",
            ]:
                from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
                    RangeVariable,
                )
                from slither.analyses.data_flow.analyses.interval.core.types.value_set import (
                    ValueSet,
                )

                # Create placeholder range variable for non-numeric parameter
                placeholder = RangeVariable(
                    interval_ranges=[],
                    valid_values=ValueSet(set()),
                    invalid_values=ValueSet(set()),
                    var_type=callee_param.type,
                )
                domain.state.add_range_variable(callee_param_name, placeholder)

    #                logger.debug(f"Created placeholder for callee parameter {callee_param_name} ({callee_param.type.name})")
    #             else:
    # #                logger.debug(
    #                     f"Skipping unsupported parameter: {callee_param.name} of type {callee_param.type}"
    #                 )

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

            # Copy constraints using the reusable method
            self._copy_constraints_between_variables(
                callee_parameter_name, caller_argument_name, domain
            )

    def _copy_constraints_between_variables(
        self, source_var_name: str, target_var_name: str, domain: IntervalDomain
    ) -> None:
        """Reusable method to copy constraints between two variables."""
        try:
            source_range_variable = domain.state.get_range_variable(source_var_name)
            if not source_range_variable:
                #                logger.debug(f"Source variable '{source_var_name}' not found in domain state")
                return

            # Copy constraints to target variable
            domain.state.set_range_variable(target_var_name, source_range_variable.deep_copy())
        #            logger.debug(f"Copied constraints from {source_var_name} to {target_var_name}")

        except Exception as e:
            logger.error(
                f"Error copying constraints from {source_var_name} to {target_var_name}: {e}"
            )
            raise

    def copy_callee_return_constraints_to_caller_variable(
        self,
        caller_return_variable: Variable,
        callee_return_values: List[Variable],
        callee_return_types: List,
        domain: IntervalDomain,
    ) -> None:
        """Copy constraints from callee function return values to caller's return variable."""
        from slither.slithir.variables.tuple import TupleVariable

        # Early return if no return variable or return types
        if not caller_return_variable or not callee_return_types:
            return

        # Handle TupleVariable (multiple return values assigned to tuple)
        if isinstance(caller_return_variable, TupleVariable):
            self._handle_tuple_return_value(
                caller_return_variable, callee_return_values, callee_return_types, domain
            )
        # Handle single return value
        elif len(callee_return_values) == 1 and len(callee_return_types) == 1:
            self._handle_single_return_value(
                caller_return_variable, callee_return_values[0], callee_return_types[0], domain
            )
        # Handle multiple return values (but not tuple variable)
        elif len(callee_return_values) > 1 and len(callee_return_types) > 1:
            self._process_multiple_return_values(
                caller_return_variable, callee_return_values, callee_return_types, domain
            )

    def _handle_single_return_value(
        self,
        caller_return_variable: Variable,
        callee_return_value: Variable,
        return_type: ElementaryType,
        domain: IntervalDomain,
    ) -> None:
        """Handle copying constraints for a single return value."""
        if not isinstance(return_type, ElementaryType) or not self.variable_manager.is_type_numeric(
            return_type
        ):
            return

        caller_return_var_name = self.variable_manager.get_variable_name(caller_return_variable)

        if isinstance(callee_return_value, Variable):
            callee_return_value_name = self.variable_manager.get_variable_name(callee_return_value)
            # Look for the return value identifier created by OperationHandler
            return_identifier = f"return_{callee_return_value_name}"
            if domain.state.has_range_variable(return_identifier):
                self._copy_constraints_between_variables(
                    return_identifier, caller_return_var_name, domain
                )
            elif domain.state.has_range_variable(callee_return_value_name):
                # Fallback to original variable name
                self._copy_constraints_between_variables(
                    callee_return_value_name, caller_return_var_name, domain
                )
        elif isinstance(callee_return_value, Constant):
            # Use constraint application manager to create constant value range variable
            self.constraint_applier.create_constant_value_range_variable(
                caller_return_var_name, callee_return_value, return_type, domain
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
                # Return value is a variable - copy constraints
                callee_var_name = self.variable_manager.get_variable_name(callee_return_value)
                if domain.state.has_range_variable(callee_var_name):
                    self._copy_constraints_between_variables(
                        callee_var_name, return_var_name, domain
                    )

    def _create_range_variable_for_literal(
        self, caller_arg: Variable, domain: IntervalDomain
    ) -> bool:
        """Create a range variable for a literal/constant argument if possible."""
        from slither.slithir.variables.constant import Constant
        from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
            RangeVariable,
        )
        from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
        from decimal import Decimal

        # Only handle constants/literals
        if not isinstance(caller_arg, Constant):
            return False

        caller_arg_name = self.variable_manager.get_variable_name(caller_arg)
        caller_arg_type = self.variable_manager.get_variable_type(caller_arg)

        # Only create range variables for numeric types
        if not self.variable_manager.is_type_numeric(caller_arg_type):
            return False

        # Convert constant value to Decimal
        constant_val = caller_arg.value
        try:
            if isinstance(constant_val, bool):
                value = Decimal(1) if constant_val else Decimal(0)
            elif isinstance(constant_val, (bytes, bytearray)):
                value = Decimal(int.from_bytes(constant_val, byteorder="big"))
            elif isinstance(constant_val, str):
                s = constant_val
                if s.startswith("0x") or s.startswith("0X"):
                    value = Decimal(int(s, 16))
                else:
                    # If it looks like hex bytecode (only hex chars, even length), parse as hex
                    hs = s.strip()
                    if len(hs) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in hs):
                        try:
                            value = Decimal(int(hs, 16))
                        except Exception:
                            value = Decimal(0)
                    else:
                        value = Decimal(str(s))
            else:
                value = Decimal(str(constant_val))

            # Create range variable with the exact value
            range_variable = RangeVariable(
                interval_ranges=None,
                valid_values=ValueSet([value]),
                invalid_values=None,
                var_type=caller_arg_type,
            )

            # Store in domain state
            domain.state.set_range_variable(caller_arg_name, range_variable)
            return True

        except (ValueError, TypeError, decimal.InvalidOperation):
            # If conversion fails, return False
            return False

    def _handle_tuple_return_value(
        self,
        caller_tuple_variable: Variable,  # TupleVariable
        callee_return_values: List[Variable],
        callee_return_types: List,
        domain: IntervalDomain,
    ) -> None:
        """Handle copying constraints for tuple return values."""
        from slither.slithir.variables.tuple import TupleVariable

        if not isinstance(caller_tuple_variable, TupleVariable):
            return

        # Process each return value and copy to corresponding tuple element
        for i, (callee_return_value, return_type) in enumerate(
            zip(callee_return_values, callee_return_types)
        ):
            # Only process numeric types
            if not (
                isinstance(return_type, ElementaryType)
                and self.variable_manager.is_type_numeric(return_type)
            ):
                continue

            # Create tuple element name matching what we created in _create_return_temporary_variables
            tuple_element_name = f"{caller_tuple_variable.name}_element_{i}"

            # Check if tuple element already exists with valid constraints
            if domain.state.has_range_variable(tuple_element_name):
                existing_range_var = domain.state.get_range_variable(tuple_element_name)
                # If the tuple element already has valid constraints (not just placeholder), don't overwrite it
                if not (
                    existing_range_var.valid_values.is_empty()
                    and existing_range_var.interval_ranges
                ):
                    logger.debug(
                        f"Tuple element {tuple_element_name} already has valid constraints, skipping overwrite"
                    )
                    continue

            if isinstance(callee_return_value, Variable):
                callee_return_value_name = self.variable_manager.get_variable_name(
                    callee_return_value
                )

                # Look for the return value identifier created by OperationHandler
                return_identifier = f"return_{callee_return_value_name}"

                if domain.state.has_range_variable(return_identifier):
                    self._copy_constraints_between_variables(
                        return_identifier, tuple_element_name, domain
                    )
                elif domain.state.has_range_variable(callee_return_value_name):
                    # Fallback to original variable name
                    self._copy_constraints_between_variables(
                        callee_return_value_name, tuple_element_name, domain
                    )
            elif isinstance(callee_return_value, Constant):
                # Use constraint application manager to create constant value range variable
                self.constraint_applier.create_constant_value_range_variable(
                    tuple_element_name, callee_return_value, return_type, domain
                )
