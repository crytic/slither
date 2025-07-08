from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.handlers.handle_arithmetic import (
    ArithmeticHandler,
)
from slither.analyses.data_flow.interval_enhanced.handlers.handle_assignment import (
    AssignmentHandler,
)

from slither.analyses.data_flow.interval_enhanced.handlers.handle_uninitialized_variable import (
    UninitializedVariableHandler,
)
from slither.core.cfg.node import Node

from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.new_elementary_type import NewElementaryType


class OperationHandler:
    def __init__(self):
        self.assignment_handler = AssignmentHandler()
        self.arithmetic_handler = ArithmeticHandler()
        self.uninitialized_variable_handler = UninitializedVariableHandler()

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:
        self.assignment_handler.handle_assignment(node, domain, operation)

    def handle_arithmetic(self, node: Node, domain: IntervalDomain, operation: Binary) -> None:
        self.arithmetic_handler.handle_arithmetic(node, domain, operation)

    def handle_uninitialized_variable(self, node: Node, domain: IntervalDomain) -> None:
        self.uninitialized_variable_handler.handle_uninitialized_variable(node, domain)
