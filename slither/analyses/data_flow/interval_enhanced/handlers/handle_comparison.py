from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager

from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary
from loguru import logger


class ComparisonHandler:
    def __init__(self, constraint_manager: ConstraintManager):
        self.constraint_manager = constraint_manager
        self.variable_manager = VariableManager()

    def handle_comparison(self, node: Node, domain: IntervalDomain, operation: Binary) -> None:
        """Handle comparison operations by adding constraints to shared manager"""
        if hasattr(operation, "lvalue") and operation.lvalue:
            var_name: str = self.variable_manager.get_variable_name(operation.lvalue)
            self.constraint_manager.add_constraint(var_name, operation)
