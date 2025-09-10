from decimal import Decimal
from typing import Union

from loguru import logger
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant


class ArithmeticHandler:
    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_arithmetic(self, node: Node, domain: IntervalDomain, operation: Binary):
        if not isinstance(operation.lvalue, Variable):
            logger.error("Arithmetic operation lvalue is not a variable")
            raise ValueError("Arithmetic operation lvalue is not a variable")

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
