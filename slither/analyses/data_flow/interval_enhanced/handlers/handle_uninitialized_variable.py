from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType


class UninitializedVariableHandler:
    def __init__(self):
        self.variable_manager = VariableManager()

    def handle_uninitialized_variable(self, node: Node, domain: IntervalDomain) -> None:
        """Handle variable declarations without initialization"""
        state_info = None
        try:
            variable = node.variable_declaration
            if variable is None:
                logger.error("Uninitialized variable is None")
                raise ValueError("Uninitialized variable is None")

            var_name = self.variable_manager.get_variable_name(variable)
            var_type = self.variable_manager.get_variable_type(variable)

            print(f"🔄 VAR TYPE: {var_type}")

            # Get the type bounds for the variable
            interval_range = self.variable_manager.get_type_bounds(var_type)

            # Create StateInfo with the type bounds interval
            # Use a safe fallback type if var_type is None
            fallback_type = None
            if var_type is None:
                try:
                    fallback_type = ElementaryType("uint256")
                except Exception as type_error:
                    logger.warning(f"Could not create fallback ElementaryType: {type_error}")
                    fallback_type = None

            try:
                state_info = StateInfo(
                    interval_ranges=[interval_range],
                    valid_values=SingleValues(),
                    invalid_values=SingleValues(),
                    var_type=var_type if var_type else fallback_type,
                )
            except Exception as state_info_error:
                logger.error(f"Error creating StateInfo: {state_info_error}")
                logger.error(f"Interval range: {interval_range}")
                logger.error(f"Var type: {var_type}")
                logger.error(f"Fallback type: {fallback_type}")
                raise

            # Add to domain
            domain.state.info[var_name] = state_info

        except Exception as e:
            logger.error(f"Error handling uninitialized variable: {e}")
            logger.error(f"Node: {node}")
            logger.error(f"Variable declaration: {getattr(node, 'variable_declaration', 'N/A')}")
            if state_info is None:
                logger.error("StateInfo was never created due to exception")
            raise
