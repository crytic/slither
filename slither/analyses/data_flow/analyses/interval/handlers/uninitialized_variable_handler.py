from typing import TYPE_CHECKING

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
            var_type = self.variable_manager.get_variable_type(variable)

            # Check if variable type is valid for processing
            if var_type is None:
                logger.error(f"Variable {var_name} has no type - implementation needed")
                raise ValueError(f"Variable {var_name} has no type - implementation needed")

            # Handle bytes variables specially by creating offset and length variables
            if self.variable_manager.is_type_bytes(var_type):
                range_variables = self.variable_manager.create_bytes_offset_and_length_variables(
                    var_name
                )
                # Add all created range variables to the domain state
                for var_name, range_variable in range_variables.items():
                    domain.state.add_range_variable(var_name, range_variable)
#                logger.debug(
                #     f"Added bytes variable {var_name} with offset and length to domain state"
                # )
            elif self.variable_manager.is_type_numeric(var_type):
                # Get the type bounds for numeric variables
                interval_range = self.variable_manager.get_type_bounds(var_type)

                # Create RangeVariable with the type bounds interval
                range_variable = RangeVariable(
                    interval_ranges=[interval_range],
                    valid_values=None,
                    invalid_values=None,
                    var_type=var_type,
                )

                # Add to domain state
                domain.state.add_range_variable(var_name, range_variable)
#                logger.debug(f"Added uninitialized variable {var_name} to domain state")
            else:
                # Gracefully handle common non-numeric types used in control flow
                if isinstance(var_type, UserDefinedType):
                    self.variable_manager.create_struct_field_variables_for_domain(
                        domain, var_name, var_type
                    )
                elif isinstance(var_type, ElementaryType) and var_type.name in [
                    "address",
                    "bool",
                    "string",
                ]:
                    # Use an opaque placeholder RangeVariable with the declared type
                    placeholder = RangeVariable(
                        interval_ranges=[],
                        valid_values=ValueSet(set()),
                        invalid_values=ValueSet(set()),
                        var_type=var_type,
                    )
                    domain.state.add_range_variable(var_name, placeholder)
#                    logger.debug(
                    #     f"Added placeholder for uninitialized non-numeric {var_type.name} variable {var_name}"
                    # )
                else:
                    logger.error(f"Variable {var_name} has unsupported type {var_type}")
                    raise ValueError(f"Variable {var_name} has unsupported type {var_type}")

        except Exception as e:
            logger.error(f"Error handling uninitialized variable: {e}")
            raise
