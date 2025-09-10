from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.handlers.assignment_handler import (
    AssignmentHandler,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.assignment import Assignment


class OperationHandler:
    def __init__(self):
        self.assignment_handler = AssignmentHandler()

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment):
        self.assignment_handler.handle_assignment(node, domain, operation)
