from typing import TYPE_CHECKING, Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node

from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.type_alias import TypeAlias, TypeAliasTopLevel
from slither.core.declarations.contract import Contract
from slither.core.solidity_types.type import Type
from slither.core.variables.variable import Variable

if TYPE_CHECKING:
    from slither.core.variables.local_variable import LocalVariable
    from slither.core.variables.state_variable import StateVariable


class UninitializedVariableHandler:
    """Handler for uninitialized variables in interval analysis."""

    def __init__(self):
        self.variable_manager = VariableInfoManager()

    def handle_uninitialized_variable(self, node: Node, domain: IntervalDomain) -> None:
        """Handle variable declarations without initialization"""
        try:
            variable = node.variable_declaration
            if variable is None:
                logger.error("Uninitialized variable is None")
                raise ValueError("Uninitialized variable is None")

            var_name = self.variable_manager.get_variable_name(variable)

            # Check if variable is already initialized in domain state
            # This can happen if local variables were initialized upfront during domain initialization
            if domain.state.has_range_variable(var_name):
                logger.debug(
                    f"Variable {var_name} already exists in domain state, skipping initialization"
                )
                return

            var_type = self.variable_manager.get_variable_type(variable)

            # Check if variable type is valid for processing
            if var_type is None:
                logger.error(f"Variable {var_name} has no type - implementation needed")
                raise ValueError(f"Variable {var_name} has no type - implementation needed")

            # Use the same comprehensive type handling as parameter initialization
            self._initialize_uninitialized_variable(variable, var_name, var_type, domain)

        except Exception as e:
            logger.error(f"Error handling uninitialized variable: {e}")
            raise

    def _initialize_uninitialized_variable(
        self,
        variable: Union["LocalVariable", "StateVariable"],
        var_name: str,
        var_type: Type,
        domain: IntervalDomain,
    ) -> None:
        """Initialize an uninitialized variable using the same logic as parameter initialization."""
        # Resolve the actual type to process (handles type aliases)
        actual_type = self._resolve_variable_type(var_type)

        if self.variable_manager.is_type_numeric(actual_type):
            self._initialize_numeric_variable(variable, var_name, actual_type, domain)
        elif self.variable_manager.is_type_bytes(actual_type):
            self._initialize_bytes_variable(variable, var_name, actual_type, domain)
        elif isinstance(var_type, ArrayType):
            self._initialize_array_variable(variable, var_name, var_type, domain)
        elif isinstance(var_type, UserDefinedType):
            self._initialize_user_defined_variable(variable, var_name, var_type, domain)
        else:
            # For other types (address, bool, string, etc.), create a placeholder
            self._create_placeholder_variable(variable, var_name, var_type, domain)

    def _resolve_variable_type(self, var_type: Type) -> Type:
        """Resolve the actual type to process, handling type aliases."""
        if isinstance(var_type, TypeAliasTopLevel):
            return var_type.type
        elif isinstance(var_type, UserDefinedType) and isinstance(var_type.type, TypeAlias):
            return var_type.type.type
        else:
            return var_type

    def _initialize_numeric_variable(
        self,
        variable: Union["LocalVariable", "StateVariable"],
        var_name: str,
        actual_type: ElementaryType,
        domain: IntervalDomain,
    ) -> None:
        """Initialize a numeric variable with interval ranges."""
        interval_range = IntervalRange(
            lower_bound=actual_type.min,
            upper_bound=actual_type.max,
        )
        range_variable = RangeVariable(
            interval_ranges=[interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=variable.type,  # Keep original type for consistency
        )
        domain.state.add_range_variable(var_name, range_variable)

    def _initialize_bytes_variable(
        self,
        variable: Union["LocalVariable", "StateVariable"],
        var_name: str,
        actual_type: ElementaryType,
        domain: IntervalDomain,
    ) -> None:
        """Initialize a bytes variable with offset and length variables."""
        range_variables = self.variable_manager.create_bytes_offset_and_length_variables(var_name)
        for nested_var_name, range_variable in range_variables.items():
            domain.state.add_range_variable(nested_var_name, range_variable)
        logger.debug(f"Added bytes uninitialized variable {var_name} to domain state")

    def _initialize_array_variable(
        self,
        variable: Union["LocalVariable", "StateVariable"],
        var_name: str,
        var_type: ArrayType,
        domain: IntervalDomain,
    ) -> None:
        """Initialize an array variable with a placeholder."""
        logger.debug(
            f"Processing ArrayType uninitialized variable: {var_name} with type {var_type}"
        )
        self._create_placeholder_variable(variable, var_name, var_type, domain)
        logger.debug(f"Added ArrayType uninitialized variable {var_name} to domain state")

    def _initialize_user_defined_variable(
        self,
        variable: Union["LocalVariable", "StateVariable"],
        var_name: str,
        var_type: UserDefinedType,
        domain: IntervalDomain,
    ) -> None:
        """Initialize a UserDefinedType variable (struct, contract, interface, or type alias)."""
        logger.debug(
            f"Processing UserDefinedType uninitialized variable: {var_name} with type {var_type}"
        )

        # Check if it's a type alias wrapped in UserDefinedType
        if isinstance(var_type.type, TypeAlias):
            logger.debug(
                f"Processing TypeAlias uninitialized variable: {var_name} with underlying type {var_type.type.type}"
            )
            actual_type = var_type.type.type
            if self.variable_manager.is_type_numeric(actual_type):
                self._initialize_numeric_variable(variable, var_name, actual_type, domain)
            elif self.variable_manager.is_type_bytes(actual_type):
                self._initialize_bytes_variable(variable, var_name, actual_type, domain)
            else:
                self._create_placeholder_variable(variable, var_name, var_type, domain)
            return

        # Check if it's an interface
        if isinstance(var_type.type, Contract) and var_type.type.is_interface:
            logger.debug(f"Creating placeholder for interface uninitialized variable: {var_name}")
            self._create_placeholder_variable(variable, var_name, var_type, domain)
            return

        # Handle structs and contracts by creating field variables
        range_variables = self.variable_manager.create_struct_field_variables(variable)

        # Add all created range variables to the domain state
        for nested_var_name, range_variable in range_variables.items():
            domain.state.add_range_variable(nested_var_name, range_variable)

        # Also create a placeholder variable for the variable itself
        # This is needed for contract types and struct types to ensure the main variable
        # is available in the domain state
        self._create_placeholder_variable(variable, var_name, var_type, domain)
        logger.debug(
            f"Added placeholder for UserDefinedType uninitialized variable {var_name} to domain state"
        )

    def _create_placeholder_variable(
        self,
        variable: Union["LocalVariable", "StateVariable"],
        var_name: str,
        var_type: Type,
        domain: IntervalDomain,
    ) -> None:
        """Create a placeholder range variable for an uninitialized variable."""
        placeholder = RangeVariable(
            interval_ranges=[],
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=var_type,
        )
        domain.state.add_range_variable(var_name, placeholder)
        logger.debug(f"Added placeholder uninitialized variable {var_name} to domain state")
