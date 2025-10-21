from typing import TYPE_CHECKING

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.array_type import ArrayType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.high_level_call import HighLevelCall

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis

from IPython import embed


class HighLevelCallHandler:
    """Handler for HighLevelCall operations (external contract calls)."""

    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_high_level_call(
        self, node: Node, domain: IntervalDomain, operation: HighLevelCall
    ) -> None:
        """Handle high-level calls by creating a RangeVariable based on the return type."""

        logger.debug(f"HighLevelCall operation: {operation}")
        logger.debug(f"HighLevelCall lvalue: {operation.lvalue}")

        # Get the result variable (lvalue) of the call
        result_variable = operation.lvalue
        if result_variable is None:
            logger.debug("HighLevelCall has no result variable, skipping")
            return

        try:
            # Get the variable name and type
            result_variable_name = self.variable_info_manager.get_variable_name(result_variable)
            result_variable_type = self.variable_info_manager.get_variable_type(result_variable)

            logger.debug(
                f"Handling HighLevelCall: {result_variable_name} = {operation.function_name}"
            )
            logger.debug(f"Variable object: {result_variable}, name: {result_variable_name}")

            # Create a RangeVariable based on the return type
            self._create_range_variable_for_call_result(
                domain, result_variable_name, result_variable_type
            )
        except Exception as e:
            logger.error(f"Error handling HighLevelCall: {e}")
            logger.error(f"Operation: {operation}")
            logger.error(f"Result variable: {result_variable}")
            raise

    def _create_range_variable_for_call_result(
        self, domain: IntervalDomain, var_name: str, var_type: ElementaryType
    ) -> None:
        """Create a RangeVariable for the result of a high-level call."""

        # Check if variable already exists
        if domain.state.has_range_variable(var_name):
            logger.debug(f"Variable {var_name} already exists in state")
            return

        # Create RangeVariable based on the return type
        if isinstance(var_type, ArrayType):
            # For array types, create a placeholder
            logger.debug(f"Creating placeholder for array type: {var_type}")
            range_variable = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
        elif self.variable_info_manager.is_type_numeric(var_type):
            # For numeric types, create a range with type bounds
            from slither.analyses.data_flow.analyses.interval.core.types.interval_range import (
                IntervalRange,
            )

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
        elif self.variable_info_manager.is_type_bytes(var_type):
            # For bytes types, create offset and length variables
            range_variables = self.variable_info_manager.create_bytes_offset_and_length_variables(
                var_name
            )
            for var_name_bytes, range_variable in range_variables.items():
                domain.state.add_range_variable(var_name_bytes, range_variable)
            return
        elif hasattr(var_type, "name") and var_type.name in ["address", "bool", "string"]:
            # For non-numeric ElementaryType types, create a placeholder
            range_variable = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
        else:
            # For other types (including UserDefinedType, etc.), create a placeholder
            logger.warning(
                f"Unsupported return type {var_type} for HighLevelCall, creating placeholder"
            )
            range_variable = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )

        # Add the range variable to the domain state
        domain.state.add_range_variable(var_name, range_variable)
        logger.debug(f"Created RangeVariable for HighLevelCall result: {var_name} ({var_type})")
        logger.debug(
            f"Added to domain state. Total variables: {len(domain.state.get_range_variables())}"
        )
