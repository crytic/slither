from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.slithir.operations.unpack import Unpack
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node
from loguru import logger


class UnpackHandler:
    def __init__(self, constraint_manager: ConstraintManager):
        self.constraint_manager = constraint_manager
        self.variable_info_manager = VariableInfoManager()

    def handle_unpack(self, node: Node, domain: IntervalDomain, operation: Unpack):
        """Handle unpacking of tuple variables by copying constraints from tuple elements to unpacked variables."""
        tuple_var = operation.tuple
        unpacked_var = operation.lvalue
        index = operation.index

        logger.info(
            f"Unpacking tuple variable {tuple_var} at index {index} into variable {unpacked_var}"
        )

        # Get the tuple variable name
        tuple_var_name = self.variable_info_manager.get_variable_name(tuple_var)

        # Get the unpacked variable name
        unpacked_var_name = self.variable_info_manager.get_variable_name(unpacked_var)

        # Look for the tuple element at the specified index
        tuple_element_name = f"{tuple_var_name}_element_{index}"

        # Check if the tuple element exists in the domain state
        if domain.state.has_range_variable(tuple_element_name):
            # Get the tuple element's range variable
            tuple_element_range_var = domain.state.get_range_variable(tuple_element_name)
            logger.debug(
                f"Retrieved tuple element {tuple_element_name} from domain state: {tuple_element_range_var}"
            )

            # Copy the constraints to the unpacked variable
            if tuple_element_range_var:
                # Create a deep copy of the tuple element's range variable
                unpacked_range_var = tuple_element_range_var.deep_copy()

                # Set the unpacked variable in the domain state
                domain.state.set_range_variable(unpacked_var_name, unpacked_range_var)

                logger.info(
                    f"Copied constraints from tuple element {tuple_element_name} to unpacked variable {unpacked_var_name}"
                )
                logger.info(f"Tuple element range variable: {tuple_element_range_var}")
                logger.info(f"Unpacked variable domain: {unpacked_range_var}")
            else:
                logger.warning(f"Tuple element {tuple_element_name} has no range variable")
        else:
            logger.warning(f"Tuple element {tuple_element_name} not found in domain state")
            # Create a placeholder range variable for the unpacked variable
            from slither.analyses.data_flow.analyses.interval.core.types.range_variable import (
                RangeVariable,
            )
            from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet

            var_type = self.variable_info_manager.get_variable_type(unpacked_var)
            placeholder = RangeVariable(
                interval_ranges=[],
                valid_values=ValueSet(set()),
                invalid_values=ValueSet(set()),
                var_type=var_type,
            )
            domain.state.set_range_variable(unpacked_var_name, placeholder)
            logger.info(f"Created placeholder for unpacked variable {unpacked_var_name}")
