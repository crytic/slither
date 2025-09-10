from decimal import Decimal
from typing import Optional

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet

from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class AssignmentHandler:
    def __init__(self):
        self.variable_info_manager = VariableInfoManager()

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:
        variable_name = self.variable_info_manager.get_variable_name(operation.lvalue)
        variable_type = self.variable_info_manager.get_variable_type(operation.lvalue)
        type_bounds = self.variable_info_manager.get_type_bounds(variable_type)

        print(variable_name, type(variable_type), variable_type, type_bounds)

        print("needs implementing")

    def _handle_temporary_assignment(
        self,
        var_name: str,
        temporary: TemporaryVariable,
        target_var: Variable,
        domain: IntervalDomain,
    ) -> None:
        print("needs implementing")

    def _handle_constant_assignment(
        self, var_name: str, constant: Constant, target_var: Variable, domain: IntervalDomain
    ) -> None:
        print("needs implementing")

    def _handle_variable_assignment(
        self, var_name: str, source_var: Variable, target_var: Variable, domain: IntervalDomain
    ) -> None:
        print("needs implementing")
