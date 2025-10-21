from decimal import Decimal
from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.new_elementary_type import NewElementaryType


class NewElementaryTypeHandler:
    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_new_elementary_type(
        self, node: Node, domain: IntervalDomain, operation: NewElementaryType
    ):
        """Handle NewElementaryType operations like 'new uint256(5)' or 'new address(0x123)'."""
        logger.info(f"Handling NewElementaryType: {operation}")

        if not operation.lvalue:
            logger.error("NewElementaryType operation has no lvalue")
            raise ValueError("NewElementaryType operation has no lvalue")

        if not isinstance(operation.lvalue, Variable):
            logger.error("NewElementaryType operation lvalue is not a variable")
            raise ValueError("NewElementaryType operation lvalue is not a variable")

        # Get the target type from the operation
        target_type = operation.type
        result_var_name = self.variable_info_manager.get_variable_name(operation.lvalue)

        logger.debug(f"Creating new {target_type} with lvalue: {result_var_name}")

        # Create a range variable for the new elementary type
        # For new elementary types, we typically initialize with a specific value or default range
        if operation.arguments:
            # If there are arguments, we need to process them to determine the initial value
            # For now, we'll create a range variable with the full type range
            # This could be enhanced to parse the actual argument values
            logger.debug(f"NewElementaryType has {len(operation.arguments)} arguments")

        # Create range variable based on the target type
        if self.variable_info_manager.is_type_numeric(target_type):
            # For numeric types, create a range variable with the full type range
            from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
                IntervalRange,
            )

            result_range = IntervalRange(
                lower_bound=Decimal(str(target_type.min)),
                upper_bound=Decimal(str(target_type.max)),
            )

            result_range_variable = RangeVariable(
                interval_ranges=[result_range],
                valid_values=None,
                invalid_values=None,
                var_type=target_type,
            )
        elif target_type.name == "bool":
            # For boolean types, create a range variable with 0 and 1 as valid values
            result_range_variable = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet({Decimal(0), Decimal(1)}),
                invalid_values=ValueSet(set()),
                var_type=target_type,
            )
        elif target_type.name == "address":
            # For address types, create a range variable with the full address range
            from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
                IntervalRange,
            )

            result_range = IntervalRange(
                lower_bound=Decimal(0),
                upper_bound=Decimal(2**160 - 1),  # Full address range
            )

            result_range_variable = RangeVariable(
                interval_ranges=[result_range],
                valid_values=None,
                invalid_values=None,
                var_type=target_type,
            )
        else:
            # For other types, create a basic range variable
            result_range_variable = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=target_type,
            )

        # Store the result in the domain state
        domain.state.set_range_variable(result_var_name, result_range_variable)
        logger.debug(f"Created new {target_type} variable: {result_var_name}")
