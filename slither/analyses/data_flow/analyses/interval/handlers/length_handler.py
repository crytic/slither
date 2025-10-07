from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.length import Length


class LengthHandler:
    """Handler for length operations on arrays and bytes."""

    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_length(self, node: Node, domain: IntervalDomain, operation: Length) -> None:
        """Handle length operation: result = array.length or bytes.length"""
        if not operation.lvalue:
            logger.error("Length operation has no lvalue")
            raise ValueError("Length operation has no lvalue")

        # Length operations return uint256
        result_type = ElementaryType("uint256")
        
        # Create a range variable for the length result
        # Use the full uint256 range since we don't know the exact length
        from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
        from decimal import Decimal
        
        result_range = IntervalRange(
            lower_bound=Decimal(str(result_type.min)),
            upper_bound=Decimal(str(result_type.max)),
        )
        
        result_range_variable = RangeVariable(
            interval_ranges=[result_range],
            valid_values=None,
            invalid_values=None,
            var_type=result_type,
        )

        # Store the result in the domain state
        result_var_name = self.variable_info_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(result_var_name, result_range_variable)
        
        logger.debug(f"Handled length operation: {operation.value}.length -> {result_var_name} (uint256)")
