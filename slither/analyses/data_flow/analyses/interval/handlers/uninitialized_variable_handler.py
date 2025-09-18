from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node


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
                self.variable_manager.create_bytes_offset_and_length_variables(var_name, domain)
                logger.debug(
                    f"Added bytes variable {var_name} with offset and length to domain state"
                )
            elif self.variable_manager.is_type_numeric(var_type):
                # Get the type bounds for numeric variables
                interval_range = self.variable_manager.get_type_bounds(var_type)

                # Create RangeVariable with the type bounds interval
                range_variable = RangeVariable(
                    interval_ranges=[interval_range],
                    valid_values=None,  # Will be initialized as empty ValueSet by RangeVariable
                    invalid_values=None,  # Will be initialized as empty ValueSet by RangeVariable
                    var_type=var_type,
                )

                # Add to domain state
                domain.state.add_range_variable(var_name, range_variable)
                logger.debug(f"Added uninitialized variable {var_name} to domain state")
            else:
                logger.warning(f"Variable {var_name} has unsupported type {var_type.name}")

        except Exception as e:
            logger.error(f"Error handling uninitialized variable: {e}")
            raise
