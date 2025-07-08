from decimal import Decimal
from typing import Optional
from loguru import logger

from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.new_elementary_type import NewElementaryType
from slither.slithir.variables.constant import Constant


class UninitializedVariableHandler:
    def __init__(self):
        self.variable_manager = VariableManager()

    def handle_uninitialized_variable(self, node: Node, domain: IntervalDomain) -> None:
        """Handle variable declarations without initialization"""
        variable = node.variable_declaration
        if variable is None:
            logger.error("Uninitialized variable is None")
            raise ValueError("Uninitialized variable is None")

        var_name = self.variable_manager.get_variable_name(variable)
        var_type = self.variable_manager.get_variable_type(variable)

        print(var_name, var_type)

        # Get the type bounds for the variable
        interval_range = self.variable_manager.get_type_bounds(var_type)

        # Create StateInfo with the type bounds interval
        state_info = StateInfo(
            interval_ranges=[interval_range],
            valid_values=SingleValues(),
            invalid_values=SingleValues(),
            var_type=var_type if var_type else ElementaryType("uint256"),
        )

        # Add to domain
        domain.state.info[var_name] = state_info
