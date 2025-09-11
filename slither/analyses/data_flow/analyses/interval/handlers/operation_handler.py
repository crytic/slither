from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.handlers.arithmetic_handler import (
    ArithmeticHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.assignment_handler import (
    AssignmentHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.comparison_handler import (
    ComparisonHandler,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary


class OperationHandler:
    def __init__(self):
        self.assignment_handler = AssignmentHandler()
        self.arithmetic_handler = ArithmeticHandler()
        self.comparison_handler = ComparisonHandler()

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment):
        self.assignment_handler.handle_assignment(node, domain, operation)

    def handle_arithmetic(self, node: Node, domain: IntervalDomain, operation: Binary):
        self.arithmetic_handler.handle_arithmetic(node, domain, operation)

    def handle_comparison(self, node: Node, domain: IntervalDomain, operation: Binary):
        self.comparison_handler.handle_comparison(node, domain, operation)
