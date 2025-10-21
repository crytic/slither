from typing import TYPE_CHECKING, Union, Optional

from loguru import logger
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
    IntervalRange,
)
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
    RangeVariable,
)
from slither.core.declarations.contract import Contract
from slither.core.declarations.structure import Structure
from slither.core.solidity_types.elementary_type import (
    Byte,
    ElementaryType,
    Fixed,
    Int,
    Ufixed,
    Uint,
)
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.variables import Variable
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain

from IPython import embed


class VariableInfoManager:
    def __init__(self):
        """Initialize the variable manager"""

    def get_variable_name(self, variable: Optional[Variable]) -> str:
        """Get canonical variable name."""
        if variable is None:
            logger.error("Variable is None")
            raise ValueError("Variable is None")

        if isinstance(variable, (StateVariable, LocalVariable)):
            return variable.canonical_name

        variable_name = getattr(variable, "name", None)
        if variable_name is None:
            logger.error(f"Variable name is None for variable: {variable}")
            raise ValueError(f"Variable name is None for variable: {variable}")

        return variable_name

    def get_variable_type(self, variable: Variable) -> ElementaryType:
        """Safely get variable type."""
        return variable.type

    def get_type_bounds(self, var_type: ElementaryType) -> IntervalRange:
        """Get type bounds using ElementaryType min/max properties."""
        if not self.is_type_numeric(var_type):
            logger.error(f"Type {var_type} is not numeric, cannot get bounds")
            raise ValueError(f"Type {var_type} is not numeric, cannot get bounds")

        try:
            # Use the min/max properties from ElementaryType
            return IntervalRange(var_type.min, var_type.max)
        except Exception as e:
            logger.error(f"Error getting bounds for type {var_type}: {e}")
            raise ValueError(f"Could not get bounds for type {var_type}: {e}")

    def is_type_numeric(self, elementary_type: ElementaryType) -> bool:
        # Check if type is numeric using ElementaryType properties
        if not elementary_type:
            logger.warning(f"Type {elementary_type} is None")
            return False

        if not isinstance(elementary_type, ElementaryType):
            return False

        try:
            type_name = elementary_type.name
            # Use the predefined lists from ElementaryType
            is_numeric = (
                type_name in Int or type_name in Uint or type_name in Fixed or type_name in Ufixed
            )

            # # logger.debug(f"Type {type_name} is numeric: {is_numeric}")
            return is_numeric
        except Exception as e:
            logger.error(f"Error checking if type {elementary_type} is numeric: {e}")
            # embed()
            raise ValueError(f"Error checking if type {elementary_type} is numeric: {e}")

    def is_type_bytes(self, elementary_type: ElementaryType) -> bool:
        # Check if type is bytes using ElementaryType properties
        if not elementary_type:
            logger.warning(f"Type {elementary_type} is None")
            return False

        if not isinstance(elementary_type, ElementaryType):
            return False

        try:
            # Handle UserDefinedType (structs) - they are not bytes
            if isinstance(elementary_type, UserDefinedType):
                return False

            type_name = elementary_type.name
            # Use the predefined Byte list from ElementaryType
            is_bytes = type_name in Byte

            # # logger.debug(f"Type {type_name} is bytes: {is_bytes}")
            return is_bytes
        except Exception as e:
            logger.warning(f"Error checking if type {elementary_type} is bytes: {e}")
            return False

    def is_type_dynamic(self, elementary_type: ElementaryType) -> bool:
        """Check if type is dynamic using ElementaryType properties."""
        if not elementary_type:
            logger.warning(f"Type {elementary_type} is None")
            return False

        try:
            # Use the is_dynamic property from ElementaryType
            is_dynamic = elementary_type.is_dynamic
            # logger.debug(f"Type {elementary_type.name} is dynamic: {is_dynamic}")
            return is_dynamic
        except Exception as e:
            logger.warning(f"Error checking if type {elementary_type} is dynamic: {e}")
            return False

    def create_bytes_offset_and_length_variables(self, var_name: str) -> dict[str, "RangeVariable"]:
        """Create offset and length variables for bytes variables.

        Returns:
            Dictionary mapping variable names to their corresponding RangeVariable objects.
        """

        range_variables = {}

        # Create a base variable for the bytes parameter itself
        # This represents the bytes parameter as a whole
        base_type = ElementaryType("uint256")  # Treat bytes as uint256 for now
        base_interval_range = IntervalRange(
            lower_bound=base_type.min,
            upper_bound=base_type.max,
        )
        base_range_variable = RangeVariable(
            interval_ranges=[base_interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=base_type,
        )
        range_variables[var_name] = base_range_variable

        # Create offset variable (uint256 type)
        offset_var_name = f"{var_name}.offset"
        offset_type = ElementaryType("uint256")
        offset_interval_range = IntervalRange(
            lower_bound=offset_type.min,
            upper_bound=offset_type.max,
        )
        offset_range_variable = RangeVariable(
            interval_ranges=[offset_interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=offset_type,
        )
        range_variables[offset_var_name] = offset_range_variable

        # Create length variable (uint256 type)
        length_var_name = f"{var_name}.length"
        length_type = ElementaryType("uint256")
        length_interval_range = IntervalRange(
            lower_bound=length_type.min,
            upper_bound=length_type.max,
        )
        length_range_variable = RangeVariable(
            interval_ranges=[length_interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=length_type,
        )
        range_variables[length_var_name] = length_range_variable

        return range_variables

    def create_struct_field_variables(self, parameter: "Variable") -> dict[str, "RangeVariable"]:
        """Create range variables for struct field variables.

        Args:
            parameter: The struct parameter variable

        Returns:
            Dictionary mapping field variable names to their corresponding RangeVariable objects.
        """

        range_variables = {}

        if not isinstance(parameter.type, UserDefinedType):
            logger.error(f"Parameter {parameter.name} is not a UserDefinedType")
            raise ValueError(f"Parameter {parameter.name} is not a UserDefinedType")

        type_def = parameter.type.type  # This could be Struct, Contract, or Enum
        # logger.debug(f"Creating field variables for: {type_def.name}")

        # Handle different types of UserDefinedType

        if isinstance(type_def, Structure):
            # Create range variables for each struct field
            for field_var in type_def.elems_ordered:
                field_name = f"{parameter.canonical_name}.{field_var.name}"
                field_type = field_var.type

                # Handle different field types
                if isinstance(field_type, ElementaryType):
                    elementary_range_variables = self._create_elementary_type_range_variable(
                        field_name, field_type
                    )
                    range_variables.update(elementary_range_variables)

                elif isinstance(field_type, UserDefinedType):
                    # Handle nested structs recursively
                    # logger.debug(f"Processing nested struct field: {field_name}")
                    # Create a temporary variable object for the nested struct field

                    nested_struct_var = LocalVariable()
                    nested_struct_var.name = field_name
                    # canonical_name is a read-only property, so we can't set it directly
                    # We'll pass the field_name directly to the recursive call
                    nested_struct_var.type = field_type

                    # Recursively create range variables for the nested struct
                    # We need to create a modified version that uses the field_name as the base
                    nested_range_variables = self._create_nested_struct_field_variables(
                        field_name, field_type
                    )
                    range_variables.update(nested_range_variables)
                    # logger.debug(f"Created nested struct field variables for: {field_name}")

                else:
                    logger.warning(
                        f"1. Non-elementary, non-struct field type {field_type} for struct field {field_name} - skipping"
                    )
                    logger.warning(
                        f"field_type: {field_type}, type: {type(field_type)}, name: {parameter.name}"
                    )
                    # embed()

        elif isinstance(type_def, Contract):
            # For contract types, create range variables for the contract's state variables
            # This allows us to track the state of the contract instance
            # logger.debug(f"Creating contract state variables for: {type_def.name}")

            for state_var in type_def.state_variables:
                # Create field variables for each state variable in the contract
                field_name = f"{parameter.canonical_name}.{state_var.name}"
                field_type = state_var.type

                # Handle different state variable types
                if isinstance(field_type, ElementaryType):
                    elementary_range_variables = self._create_elementary_type_range_variable(
                        field_name, field_type
                    )
                    range_variables.update(elementary_range_variables)

                elif isinstance(field_type, UserDefinedType):
                    # Handle nested structs/enums/contracts in state variables
                    # logger.debug(f"Processing nested type in contract state variable: {field_name}")
                    nested_range_variables = self._create_nested_struct_field_variables(
                        field_name, field_type
                    )
                    range_variables.update(nested_range_variables)
                    # logger.debug(f"Created nested type variables for contract state: {field_name}")

                else:
                    logger.warning(
                        f"2. Non-elementary, non-user-defined state variable type {field_type} for contract field {field_name} - skipping"
                    )

        else:
            logger.warning(f"Unsupported UserDefinedType: {type_def}")
            return range_variables

        return range_variables

    def create_struct_field_variables_for_domain(
        self, domain: "IntervalDomain", var_name: str, var_type: UserDefinedType
    ) -> None:
        """Create and add struct field variables directly to domain state.

        This is a convenience method for handlers that need to create struct field
        variables and add them to the domain state in one operation.
        """

        if not hasattr(var_type.type, "elems"):
            # logger.debug(f"Struct type {var_type} has no elements")
            return

        for field_name, field_type in var_type.type.elems.items():
            field_var_name = f"{var_name}.{field_name}"

            # Skip if field variable already exists
            if domain.state.has_range_variable(field_var_name):
                # logger.debug(f"Field variable {field_var_name} already exists")
                continue

            # Get the actual field type from the struct definition
            actual_field_type = field_type.type if hasattr(field_type, "type") else field_type

            # Recursively handle nested structs
            if isinstance(actual_field_type, UserDefinedType):
                self.create_struct_field_variables_for_domain(
                    domain, field_var_name, actual_field_type
                )
            elif self.is_type_numeric(actual_field_type):
                # Create numeric range variable
                interval_range = IntervalRange(
                    lower_bound=actual_field_type.min,
                    upper_bound=actual_field_type.max,
                )
                range_variable = RangeVariable(
                    interval_ranges=[interval_range],
                    valid_values=None,
                    invalid_values=None,
                    var_type=actual_field_type,
                )
                domain.state.add_range_variable(field_var_name, range_variable)
                # logger.debug(f"Created numeric field variable {field_var_name}")
            elif self.is_type_bytes(actual_field_type):
                # Create bytes range variables
                range_variables = self.create_bytes_offset_and_length_variables(field_var_name)
                for var_name_bytes, range_variable in range_variables.items():
                    domain.state.add_range_variable(var_name_bytes, range_variable)
                # logger.debug(f"Created bytes field variable {field_var_name}")
            # else:
            #     # logger.debug(
            #         f"Skipping unsupported field type {actual_field_type} for {field_var_name}"
            #     )

        # logger.debug(f"Created struct field variables for {var_name}")

    def _create_elementary_type_range_variable(
        self, field_name: str, field_type: ElementaryType
    ) -> dict[str, "RangeVariable"]:
        """Create range variables for elementary types (numeric, bytes, etc.).

        Args:
            field_name: The name of the field
            field_type: The ElementaryType of the field

        Returns:
            Dictionary mapping field variable names to their corresponding RangeVariable objects.
        """
        range_variables = {}

        if self.is_type_numeric(field_type):
            # Create interval range with type bounds for numeric fields
            interval_range = IntervalRange(
                lower_bound=field_type.min,
                upper_bound=field_type.max,
            )
            range_variable = RangeVariable(
                interval_ranges=[interval_range],
                valid_values=None,
                invalid_values=None,
                var_type=field_type,
            )
            range_variables[field_name] = range_variable
            # logger.debug(f"Created numeric field variable: {field_name} -> {field_type}")

        elif self.is_type_bytes(field_type):
            # For bytes fields, create offset and length variables
            bytes_range_variables = self.create_bytes_offset_and_length_variables(field_name)
            range_variables.update(bytes_range_variables)
            # logger.debug(f"Created bytes field variables for: {field_name}")

        else:
            logger.warning(f"Unsupported field type {field_type} for field {field_name}")

        return range_variables

    def _create_nested_struct_field_variables(
        self, base_name: str, field_type: "UserDefinedType"
    ) -> dict[str, "RangeVariable"]:
        """Create range variables for nested struct fields.

        Args:
            base_name: The base name for the nested struct field
            field_type: The UserDefinedType for the nested struct

        Returns:
            Dictionary mapping field variable names to their corresponding RangeVariable objects.
        """

        range_variables = {}
        struct_def = field_type.type  # This is the Struct object

        # Create range variables for each struct field
        for field_var in struct_def.elems_ordered:
            field_name = f"{base_name}.{field_var.name}"
            field_type = field_var.type

            # Handle different field types
            if isinstance(field_type, ElementaryType):
                elementary_range_variables = self._create_elementary_type_range_variable(
                    field_name, field_type
                )
                range_variables.update(elementary_range_variables)

            elif isinstance(field_type, UserDefinedType):
                # Handle deeply nested structs recursively
                # logger.debug(f"Processing deeply nested struct field: {field_name}")
                nested_range_variables = self._create_nested_struct_field_variables(
                    field_name, field_type
                )
                range_variables.update(nested_range_variables)
                # logger.debug(f"Created deeply nested struct field variables for: {field_name}")

            else:
                logger.warning(
                    f"3. Non-elementary, non-struct nested field type {field_type} for struct field {field_name} - skipping"
                )

        return range_variables
