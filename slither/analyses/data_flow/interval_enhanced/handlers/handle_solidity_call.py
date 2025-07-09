from typing import List

from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.slithir.operations.solidity_call import SolidityCall


class SolidityCallHandler:
    def __init__(self, constraint_manager: ConstraintManager):
        self.constraint_manager = constraint_manager
        self.variable_manager = VariableManager()

    def handle_solidity_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        """Handle comparison operations by adding constraints to shared manager"""
        require_assert_functions: List[str] = [
            "require(bool)",
            "assert(bool)",
            "require(bool,string)",
            "require(bool,error)",
        ]

        if operation.function.name not in require_assert_functions:
            return

        if operation.arguments and len(operation.arguments) > 0:
            condition_variable = operation.arguments[0]
            self.constraint_manager.apply_constraint_from_variable(condition_variable, domain)
