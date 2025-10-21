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
from slither.slithir.operations.unary import Unary, UnaryType, logger

from IPython import embed


class UnaryHandler:
    def __init__(
        self, constraint_storage: ConstraintManager = None
    ):  # pyright: ignore[reportUndefinedVariable]
        # Use provided constraint storage or create a new one
        if constraint_storage is not None:
            self.constraint_storage = constraint_storage
        else:
            self.constraint_storage = ConstraintManager()
        self.variable_info_manager = VariableInfoManager()

    def handle_unary(self, node: Node, domain: IntervalDomain, operation: Unary):
        print(f"Unary operation: {operation}")

        if operation.type != UnaryType.BANG:
            logger.error(f"Unsupported unary operation: {operation.type}")
            embed()
            raise ValueError(f"Unsupported unary operation: {operation.type}")

        if operation.lvalue is None:
            logger.error("Unary operation lvalue is None")
            raise ValueError("Unary operation lvalue is None")

        # Store the unary operation constraint for future use
        logger.warning(f"Storing unary operation constraint for variable {operation.lvalue}")
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
