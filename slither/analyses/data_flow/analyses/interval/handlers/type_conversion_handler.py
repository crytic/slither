from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.type_conversion import TypeConversion

from IPython import embed


class TypeConversionHandler:
    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_type_conversion(self, node: Node, domain: IntervalDomain, operation: TypeConversion):
        """Handle type conversion operations like TMP_4 = CONVERT 0 to address."""

        if not isinstance(operation.lvalue, Variable):
            logger.error("Type conversion operation lvalue is not a variable")
            raise ValueError("Type conversion operation lvalue is not a variable")

        # Get the source variable info
        logger.info(f"Getting range information for source variable: {operation.variable}")
        source_variable_range = RangeVariable.get_variable_info(domain, operation.variable, node)

        # Create a new range variable with the target type
        result_range_variable = RangeVariable(
            interval_ranges=source_variable_range.interval_ranges.copy(),
            valid_values=source_variable_range.valid_values,
            invalid_values=source_variable_range.invalid_values,
            var_type=operation.type,  # Use the target type from the conversion
        )

        # Set the result variable in the domain
        result_variable_name = self.variable_info_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(
            name=result_variable_name, range_variable=result_range_variable
        )

        logger.debug(
            f"Handled type conversion: {result_variable_name} = CONVERT {operation.variable} to {operation.type}"
        )
