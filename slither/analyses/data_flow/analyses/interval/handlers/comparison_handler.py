from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary, BinaryType


class ComparisonHandler:
    """Handler for comparison operations in interval analysis."""

    def __init__(self, constraint_storage: ConstraintManager = None):
        # Use provided constraint storage or create a new one
        if constraint_storage is not None:
            self.constraint_storage = constraint_storage
        else:
            self.constraint_storage = ConstraintManager()
        self.variable_info_manager = VariableInfoManager()

    def handle_comparison(self, node: Node, domain: IntervalDomain, operation: Binary):
        # Check if this is a valid comparison operation
        valid_comparison_types = {
            BinaryType.GREATER,
            BinaryType.LESS,
            BinaryType.GREATER_EQUAL,
            BinaryType.LESS_EQUAL,
            BinaryType.EQUAL,
            BinaryType.NOT_EQUAL,
        }

        if operation.type not in valid_comparison_types:
            logger.error("Comparison operation type is not a valid comparison type")
            raise ValueError("Comparison operation type is not a valid comparison type")

        if operation.lvalue is None:
            logger.error("Comparison operation lvalue is None")
            raise ValueError("Comparison operation lvalue is None")

        # Store the comparison operation constraint for future use
        logger.warning(f"Storing comparison operation constraint for variable {operation.lvalue}")
        self.constraint_storage.store_comparison_operation_constraint(operation, domain)

        # Create a range variable for the comparison result (boolean)
        temp_var_name = self.variable_info_manager.get_variable_name(operation.lvalue)
        # Comparison results are boolean (0 or 1)

        range_variable = RangeVariable(
            interval_ranges=None,
            valid_values=ValueSet({0, 1}),  # Boolean can be 0 or 1
            invalid_values=ValueSet(set()),
            var_type=ElementaryType("bool"),
        )
        domain.state.set_range_variable(temp_var_name, range_variable)
