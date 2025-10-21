from decimal import Decimal
from typing import TYPE_CHECKING

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.handlers.arithmetic_handler import (
    ArithmeticHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.assignment_handler import (
    AssignmentHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.comparison_handler import (
    ComparisonHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.high_level_call_handler import (
    HighLevelCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.internal_call_handler import (
    InternalCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.internal_dynamic_call_handler import (
    InternalDynamicCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.library_call_handler import (
    LibraryCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.new_elementary_type_handler import (
    NewElementaryTypeHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.solidity_call_handler import (
    SolidityCallHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.unary_handler import UnaryHandler
from slither.analyses.data_flow.analyses.interval.handlers.uninitialized_variable_handler import (
    UninitializedVariableHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.member_handler import (
    MemberHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.length_handler import (
    LengthHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.type_conversion_handler import (
    TypeConversionHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.index_handler import (
    IndexHandler,
)
from slither.analyses.data_flow.analyses.interval.handlers.unpack_handler import UnpackHandler
from slither.analyses.data_flow.analyses.interval.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.analyses.data_flow.analyses.interval.managers.reference_handler import (
    ReferenceHandler,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.internal_dynamic_call import InternalDynamicCall
from slither.slithir.operations.length import Length
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.member import Member
from slither.slithir.operations.new_elementary_type import NewElementaryType
from slither.slithir.operations.solidity_call import SolidityCall
from slither.slithir.operations.type_conversion import TypeConversion
from slither.slithir.operations.index import Index
from slither.slithir.operations.unary import Unary
from slither.slithir.operations.unpack import Unpack

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis


class OperationHandler:
    def __init__(self, reference_handler: ReferenceHandler, constraint_manager=None):
        # Use shared constraint manager if provided, otherwise create a new one
        if constraint_manager is not None:
            self.shared_constraint_storage = constraint_manager  # Same instance!
        else:
            self.shared_constraint_storage = ConstraintManager()
        self.variable_info_manager = VariableInfoManager()
        self.reference_handler = reference_handler

        self.assignment_handler = AssignmentHandler()
        self.arithmetic_handler = ArithmeticHandler(self.shared_constraint_storage)
        self.comparison_handler = ComparisonHandler(self.shared_constraint_storage)
        self.uninitialized_variable_handler = UninitializedVariableHandler()
        self.solidity_call_handler = SolidityCallHandler(self.shared_constraint_storage)
        self.internal_call_handler = InternalCallHandler(self.shared_constraint_storage)
        self.library_call_handler = LibraryCallHandler(self.shared_constraint_storage)
        self.high_level_call_handler = HighLevelCallHandler()
        self.member_handler = MemberHandler(self.reference_handler)
        self.length_handler = LengthHandler()
        self.type_conversion_handler = TypeConversionHandler()
        self.index_handler = IndexHandler(self.reference_handler)
        self.unary_handler = UnaryHandler(self.shared_constraint_storage)
        self.internal_dynamic_call_handler = InternalDynamicCallHandler(
            self.shared_constraint_storage
        )
        self.unpack_handler = UnpackHandler(self.shared_constraint_storage)
        self.new_elementary_type_handler = NewElementaryTypeHandler()

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

    def handle_high_level_call(self, node: Node, domain: IntervalDomain, operation: HighLevelCall):
        self.high_level_call_handler.handle_high_level_call(node, domain, operation)

    def handle_length(self, node: Node, domain: IntervalDomain, operation: Length):
        self.length_handler.handle_length(node, domain, operation)

    def handle_type_conversion(self, node: Node, domain: IntervalDomain, operation: TypeConversion):
        self.type_conversion_handler.handle_type_conversion(node, domain, operation)

    def handle_index(self, node: Node, domain: IntervalDomain, operation: Index):
        self.index_handler.handle_index(node, domain, operation)

    def handle_boolean(self, node: Node, domain: IntervalDomain, operation: Binary):
        """Handle boolean operations by creating a temporary variable for the result."""
        valid_boolean_types = {
            BinaryType.ANDAND,
            BinaryType.OROR,
        }

        if operation.type not in valid_boolean_types:
            logger.error("Boolean operation type is not a valid boolean type")
        if operation.lvalue is None:
            logger.error("Boolean operation lvalue is None")
            raise ValueError("Boolean operation lvalue is None")

        # Store the boolean operation constraint for future use
        logger.warning(f"Storing boolean operation constraint for variable {operation.lvalue}")
        self.shared_constraint_storage.store_comparison_operation_constraint(operation, domain)

        # Create a range variable for the boolean result (0 or 1)
        temp_var_name = self.variable_info_manager.get_variable_name(operation.lvalue)

        logger.info(f"Created boolean temporary variable: {temp_var_name}")

        range_variable = RangeVariable(
            interval_ranges=[],
            valid_values=ValueSet({Decimal(0), Decimal(1)}),  # Boolean can be 0 or 1
            invalid_values=ValueSet(set()),
            var_type=ElementaryType("bool"),
        )
        domain.state.set_range_variable(temp_var_name, range_variable)

    def handle_unary(self, node: Node, domain: IntervalDomain, operation: Unary):
        self.unary_handler.handle_unary(node, domain, operation)

    def handle_internal_dynamic_call(
        self, node: Node, domain: IntervalDomain, operation: InternalDynamicCall
    ):

        self.internal_dynamic_call_handler.handle_internal_dynamic_call(node, domain, operation)

    def handle_unpack(self, node: Node, domain: IntervalDomain, operation: Unpack):
        self.unpack_handler.handle_unpack(node, domain, operation)

    def handle_new_elementary_type(
        self, node: Node, domain: IntervalDomain, operation: NewElementaryType
    ):
        self.new_elementary_type_handler.handle_new_elementary_type(node, domain, operation)
