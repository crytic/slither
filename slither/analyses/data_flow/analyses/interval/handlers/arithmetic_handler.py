from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary


class ArithmeticHandler:
    def __init__(self, constraint_storage=None):
        self.variable_info_manager = VariableInfoManager()
        self.constraint_storage = constraint_storage

    def handle_arithmetic(self, node: Node, domain: IntervalDomain, operation: Binary):
        if not isinstance(operation.lvalue, Variable):
            logger.error("Arithmetic operation lvalue is not a variable")
            raise ValueError("Arithmetic operation lvalue is not a variable")

        logger.info(f"Handling arithmetic operation: {operation}")
        left_variable_range = RangeVariable.get_variable_info(domain, operation.variable_left)
        right_variable_range = RangeVariable.get_variable_info(domain, operation.variable_right)

        # Calculate the result
        result_range_variable = RangeVariable.compute_arithmetic_range_variable(
            left=left_variable_range,
            right=right_variable_range,
            operation_type=operation.type,
        )

        result_variable_name = self.variable_info_manager.get_variable_name(operation.lvalue)
        domain.state.set_range_variable(
            name=result_variable_name, range_variable=result_range_variable
        )

        # Don't store arithmetic operations as constraints
        # Only comparison operations should be stored as constraints
        # Arithmetic operations are computation results, not comparison constraints
