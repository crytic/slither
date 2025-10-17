from typing import Optional

from loguru import logger

from slither.core.cfg.node import Node
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.analyses.data_flow.analyses.interval.managers.reference_handler import (
    ReferenceHandler,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.user_defined_type import UserDefinedType
from slither.slithir.operations.index import Index


class IndexHandler:
    """Handler for Index operations (e.g., array[index], mapping[key])."""

    def __init__(self, reference_handler: ReferenceHandler) -> None:
        self._variable_info_manager = VariableInfoManager()
        self._reference_handler = reference_handler

    def handle_index(self, node: Node, domain: IntervalDomain, operation: Index) -> None:
        """Handle Index operations by creating appropriate range variables and tracking references."""
        logger.debug(f"IndexHandler.handle_index called for operation: {operation}")

        if not operation.lvalue:
            raise ValueError("Index operation has no lvalue")

        result_var_name = self._variable_info_manager.get_variable_name(operation.lvalue)
        result_type = operation.lvalue.type

        logger.debug(f"Processing Index operation: {result_var_name} with type {result_type}")

        # Create the appropriate range variable
        self._create_range_variable(domain, result_var_name, result_type, operation)

    def _create_range_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType, operation: Index
    ) -> None:
        """Create and add a range variable to the domain state."""
        logger.debug(f"Creating range variable: {var_name} with type {var_type}")

        # Check if variable already exists
        if domain.state.has_range_variable(var_name):
            logger.debug(f"Variable {var_name} already exists in state")
            return

        # Handle struct types - recursively create range variables for their fields
        if isinstance(var_type, UserDefinedType):
            logger.debug(f"Creating struct field variables for {var_name}")
            self._variable_info_manager.create_struct_field_variables_for_domain(
                domain, var_name, var_type
            )
            # Also create a placeholder variable for the struct itself
            logger.debug(f"Creating placeholder variable for struct {var_name}")
            placeholder = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
            domain.state.add_range_variable(var_name, placeholder)
            logger.debug(f"Created placeholder variable {var_name} with type {var_type}")
            return

        # Create the appropriate range variable based on type
        if self._variable_info_manager.is_type_numeric(var_type):
            logger.debug(f"Creating numeric variable for {var_name}")
            self._create_numeric_variable(domain, var_name, var_type)
        elif self._variable_info_manager.is_type_bytes(var_type):
            logger.debug(f"Creating bytes variable for {var_name}")
            self._create_bytes_variable(domain, var_name, var_type)
        else:
            # For all other types (address, bool, string, etc.), create a placeholder
            logger.debug(f"Creating placeholder variable for {var_name} with type {var_type}")
            placeholder = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
            domain.state.add_range_variable(var_name, placeholder)
            logger.debug(f"Created placeholder variable {var_name} with type {var_type}")

    def _create_numeric_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType
    ) -> None:
        """Create a numeric range variable."""
        logger.debug(f"Creating numeric variable: {var_name} with type {var_type}")

        # Index operations create independent variables with type bounds
        # They don't inherit from other variables since array[index] is a dynamic access
        interval_range = IntervalRange(
            lower_bound=var_type.min,
            upper_bound=var_type.max,
        )
        range_variable = RangeVariable(
            interval_ranges=[interval_range],
            valid_values=None,
            invalid_values=None,
            var_type=var_type,
        )

        domain.state.add_range_variable(var_name, range_variable)
        logger.debug(f"Successfully added numeric variable {var_name} to domain state")

        # Verify the variable was actually added
        if domain.state.has_range_variable(var_name):
            logger.debug(f"Verification: Variable {var_name} exists in domain state")
        else:
            logger.error(f"Verification failed: Variable {var_name} does NOT exist in domain state")

    def _create_bytes_variable(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType
    ) -> None:
        """Create bytes range variables (offset and length)."""
        range_variables = self._variable_info_manager.create_bytes_offset_and_length_variables(
            var_name
        )
        # Add all created range variables to the domain state
        for var_name_bytes, range_variable in range_variables.items():
            domain.state.add_range_variable(var_name_bytes, range_variable)
        logger.debug(f"Created bytes variable {var_name} with type {var_type}")
