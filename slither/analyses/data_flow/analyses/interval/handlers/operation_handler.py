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
from slither.analyses.data_flow.analyses.interval.handlers.solidity_call_handler import (
    SolidityCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.uninitialized_variable_handler import (
    UninitializedVariableHandler,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.solidity_call import SolidityCall


class OperationHandler:
    def __init__(self):
        self.assignment_handler = AssignmentHandler()
        self.arithmetic_handler = ArithmeticHandler()
        self.comparison_handler = ComparisonHandler()
        self.uninitialized_variable_handler = UninitializedVariableHandler()
        self.solidity_call_handler = SolidityCallHandler()

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment):
        self.assignment_handler.handle_assignment(node, domain, operation)

    def handle_arithmetic(self, node: Node, domain: IntervalDomain, operation: Binary):
        self.arithmetic_handler.handle_arithmetic(node, domain, operation)

    def handle_comparison(self, node: Node, domain: IntervalDomain, operation: Binary):
        self.comparison_handler.handle_comparison(node, domain, operation)

    def handle_uninitialized_variable(self, node: Node, domain: IntervalDomain):
        self.uninitialized_variable_handler.handle_uninitialized_variable(node, domain)

    def handle_solidity_call(self, node: Node, domain: IntervalDomain, operation: SolidityCall):
        self.solidity_call_handler.handle_solidity_call(node, domain, operation)
