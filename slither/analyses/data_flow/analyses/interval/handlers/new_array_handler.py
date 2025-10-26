from decimal import Decimal

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
    IntervalRange,
)
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
    RangeVariable,
)
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.new_array import NewArray


class NewArrayHandler:
    """Handler for NewArray operations like 'new PoolInfo[](length)'."""

    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_new_array(
        self, node: Node, domain: IntervalDomain, operation: NewArray
    ):
        """Handle NewArray operations by creating appropriate range variables."""
        logger.info(f"Handling NewArray: {operation}")

        if not operation.lvalue:
            logger.error("NewArray operation has no lvalue")
            raise ValueError("NewArray operation has no lvalue")

        # Get the array variable name that will hold the newly created array
        array_var_name = self.variable_info_manager.get_variable_name(operation.lvalue)

        # Get the array type
        array_type = operation.array_type

        logger.debug(f"Creating new array: {array_var_name} of type {array_type}")

        # Create a placeholder range variable for the array
        # Individual elements are accessed via Index operations and handled separately
        array_range_variable = RangeVariable(
            interval_ranges=[],  # Arrays don't have numeric intervals
            valid_values=ValueSet(set()),
            invalid_values=ValueSet(set()),
            var_type=array_type,
        )

        # Store the array variable in the domain state
        domain.state.set_range_variable(array_var_name, array_range_variable)

        logger.debug(f"Created array variable: {array_var_name}")

        # Create array length variable with the range from the length argument
        self._create_array_length_variable(
            array_var_name, domain, operation
        )

    def _create_array_length_variable(
        self, array_var_name: str, domain: IntervalDomain, operation: NewArray
    ) -> None:
        """Create an array.length variable with the appropriate range."""
        # Get the length argument from the operation (e.g., 'length' in 'new PoolInfo[](length)')
        if not operation.arguments:
            logger.debug(f"No length argument provided for array {array_var_name}")
            return

        # For dynamic arrays, the length is passed as the first argument
        length_arg = operation.arguments[0]
        length_arg_name = self.variable_info_manager.get_variable_name(length_arg)

        logger.debug(f"Array {array_var_name} has length argument: {length_arg_name}")

        # Create array.length variable name
        array_length_name = f"{array_var_name}.length"

        # Get the range of the length argument from the domain state
        length_arg_range_var = domain.state.get_range_variable(length_arg_name)

        if length_arg_range_var is not None:
            # If we have information about the length argument's range, create the array.length variable with it
            length_type = ElementaryType("uint256")
            
            # Get valid and invalid values
            valid_values = length_arg_range_var.get_valid_values()
            invalid_values = length_arg_range_var.get_invalid_values()
            
            # Convert to a set for ValueSet initialization
            valid_values_set = set(valid_values) if valid_values else set()
            invalid_values_set = set(invalid_values) if invalid_values else set()
            
            # Create a copy of the length argument's range
            array_length_range_var = RangeVariable(
                interval_ranges=[
                    range.copy() for range in length_arg_range_var.get_interval_ranges()
                ],
                valid_values=ValueSet(valid_values_set),
                invalid_values=ValueSet(invalid_values_set),
                var_type=length_type,
            )
            
            domain.state.set_range_variable(array_length_name, array_length_range_var)
            logger.debug(
                f"Created array.length variable: {array_length_name} with range {length_arg_range_var.get_interval_ranges()}"
            )
        else:
            # If we don't have information about the length argument, create a default uint256 range
            length_type = ElementaryType("uint256")
            default_range = IntervalRange(
                lower_bound=Decimal(str(length_type.min)),
                upper_bound=Decimal(str(length_type.max)),
            )
            
            array_length_range_var = RangeVariable(
                interval_ranges=[default_range],
                valid_values=None,
                invalid_values=None,
                var_type=length_type,
            )
            
            domain.state.set_range_variable(array_length_name, array_length_range_var)
            logger.debug(
                f"Created array.length variable: {array_length_name} with default uint256 range"
            )