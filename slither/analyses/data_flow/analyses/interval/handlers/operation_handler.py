from typing import TYPE_CHECKING

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
from slither.analyses.data_flow.analyses.interval.handlers.internal_call_handler import (
    InternalCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.library_call_handler import (
    LibraryCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.solidity_call_handler import (
    SolidityCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.uninitialized_variable_handler import (
    UninitializedVariableHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.member_handler import (
    MemberHandler,
)
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.member import Member
from slither.slithir.operations.solidity_call import SolidityCall

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis


class OperationHandler:
    def __init__(self):
        # Create a shared constraint storage for all handlers
        self.shared_constraint_storage = ConstraintManager()

        self.assignment_handler = AssignmentHandler()
        self.arithmetic_handler = ArithmeticHandler(self.shared_constraint_storage)
        self.comparison_handler = ComparisonHandler(self.shared_constraint_storage)
        self.uninitialized_variable_handler = UninitializedVariableHandler()
        self.solidity_call_handler = SolidityCallHandler(self.shared_constraint_storage)
        self.internal_call_handler = InternalCallHandler(self.shared_constraint_storage)
        self.library_call_handler = LibraryCallHandler(self.shared_constraint_storage)
        self.member_handler = MemberHandler()

        # Update constraint manager with member handler for constraint propagation
        self.shared_constraint_storage.constraint_applier.member_handler = self.member_handler

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

    def handle_internal_call(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: InternalCall,
        analysis_instance: "IntervalAnalysis",
    ):
        self.internal_call_handler.handle_internal_call(node, domain, operation, analysis_instance)

    def handle_member(self, node: Node, domain: IntervalDomain, operation: Member):
        self.member_handler.handle_member(node, domain, operation)

    def handle_library_call(
        self,
        node: Node,
        domain: IntervalDomain,
        operation: LibraryCall,
        analysis_instance: "IntervalAnalysis",
    ):
        self.library_call_handler.handle_library_call(node, domain, operation, analysis_instance)