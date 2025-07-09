from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.handlers.handle_arithmetic import (
    ArithmeticHandler,
)
from slither.analyses.data_flow.interval_enhanced.handlers.handle_assignment import (
    AssignmentHandler,
)

from slither.analyses.data_flow.interval_enhanced.handlers.handle_comparison import (
    ComparisonHandler,
)
from slither.analyses.data_flow.interval_enhanced.handlers.handle_solidity_call import (
    SolidityCallHandler,
)
from slither.analyses.data_flow.interval_enhanced.handlers.handle_uninitialized_variable import (
    UninitializedVariableHandler,
)
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node

from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.solidity_call import SolidityCall


class OperationHandler:
    def __init__(self, constraint_manager: ConstraintManager):
        self.assignment_handler = AssignmentHandler(constraint_manager=constraint_manager)
        self.arithmetic_handler = ArithmeticHandler()
        self.uninitialized_variable_handler = UninitializedVariableHandler()
        self.comparison_handler = ComparisonHandler(constraint_manager)
        self.solidity_call_handler = SolidityCallHandler(constraint_manager)

    def handle_assignment(self, node: Node, domain: IntervalDomain, operation: Assignment) -> None:
        self.assignment_handler.handle_assignment(node, domain, operation)

    def handle_arithmetic(self, node: Node, domain: IntervalDomain, operation: Binary) -> None:
        self.arithmetic_handler.handle_arithmetic(node, domain, operation)

    def handle_uninitialized_variable(self, node: Node, domain: IntervalDomain) -> None:
        self.uninitialized_variable_handler.handle_uninitialized_variable(node, domain)

    def handle_comparison(self, node: Node, domain: IntervalDomain, operation: Binary) -> None:
        self.comparison_handler.handle_comparison(node, domain, operation)

    def handle_solidity_call(
        self, node: Node, domain: IntervalDomain, operation: SolidityCall
    ) -> None:
        self.solidity_call_handler.handle_solidity_call(node, domain, operation)
