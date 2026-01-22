from typing import Optional, Union

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
    RoundingState,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.return_operation import Return
from slither.slithir.variables.constant import Constant


class RoundingAnalysis(Analysis):
    """Analysis that tracks rounding direction metadata through data flow"""

    def __init__(self):
        self._direction = Forward()

    def domain(self) -> Domain:
        return RoundingDomain.bottom()

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return RoundingDomain.bottom()

    def transfer_function(self, node: Node, domain: RoundingDomain, operation: Operation):
        """Core analysis logic - tag operations and propagate rounding metadata"""
        if domain.variant == DomainVariant.BOTTOM:
            domain.variant = DomainVariant.STATE
            domain.state = RoundingState()

        if operation is None:
            return

        self._analyze_operation_by_type(operation, domain)

    def _analyze_operation_by_type(self, operation: Operation, domain: RoundingDomain):
        """Route operation to appropriate handler"""
        if isinstance(operation, Binary):
            self._handle_binary_operation(operation, domain)
        elif isinstance(operation, Assignment):
            self._handle_assignment_operation(operation, domain)
        elif isinstance(operation, (InternalCall, HighLevelCall, LibraryCall)):
            self._handle_function_call(operation, domain)
        elif isinstance(operation, Return):
            # Return operations don't change rounding tags, just propagate
            pass

    def _handle_binary_operation(self, operation: Binary, domain: RoundingDomain):
        """Handle arithmetic binary operations"""
        if not operation.lvalue:
            return

        result_var = operation.lvalue
        left_var = operation.variable_left
        right_var = operation.variable_right
        op_type = operation.type

        if op_type == BinaryType.DIVISION:
            # Plain division (/) always truncates (rounds down) by convention
            # If developers want UP rounding, they should use explicit functions like divUp()
            # So plain division is always DOWN, regardless of dividend's tag
            domain.state.set_tag(result_var, RoundingTag.DOWN)

        elif op_type == BinaryType.ADDITION:
            tag = self._combine_tags(
                self._get_variable_tag(left_var, domain),
                self._get_variable_tag(right_var, domain),
            )
            domain.state.set_tag(result_var, tag)

        elif op_type == BinaryType.SUBTRACTION:
            tag = self._combine_tags(
                self._get_variable_tag(left_var, domain),
                self._get_variable_tag(right_var, domain),
            )
            domain.state.set_tag(result_var, tag)

        elif op_type == BinaryType.MULTIPLICATION:
            tag = self._combine_tags(
                self._get_variable_tag(left_var, domain),
                self._get_variable_tag(right_var, domain),
            )
            domain.state.set_tag(result_var, tag)

        # Other binary operations (comparisons, bitwise, etc.) don't affect rounding
        # so we leave result as UNKNOWN (default)

    def _handle_assignment_operation(self, operation: Assignment, domain: RoundingDomain):
        """Handle assignment: propagate tag from right side to left side"""
        if not operation.lvalue:
            return

        rvalue = operation.rvalue
        if isinstance(rvalue, Variable):
            tag = self._get_variable_tag(rvalue, domain)
            domain.state.set_tag(operation.lvalue, tag)
        # For non-variable rvalues (functions, tuples), leave as UNKNOWN

    def _handle_function_call(
        self,
        operation: Union[InternalCall, HighLevelCall, LibraryCall],
        domain: RoundingDomain,
    ):
        """Handle function calls - infer rounding from function name"""
        if not operation.lvalue:
            return

        # Get function name
        func_name = ""
        if isinstance(operation, InternalCall):
            if operation.function:
                func_name = operation.function.name
            elif hasattr(operation, "function_name"):
                func_name = str(operation.function_name)
        elif isinstance(operation, (HighLevelCall, LibraryCall)):
            if hasattr(operation.function_name, "value"):
                func_name = operation.function_name.value
            elif hasattr(operation.function_name, "name"):
                func_name = operation.function_name.name
            else:
                func_name = str(operation.function_name)

        # Infer tag from function name
        tag = self._infer_tag_from_name(func_name)
        domain.state.set_tag(operation.lvalue, tag)

    def _infer_tag_from_name(self, function_name: str) -> RoundingTag:
        """
        Infer rounding direction from function name.
        Checks for indicators like "down", "floor", "up", "ceil" in the name.
        """
        name_lower = function_name.lower()
        if "down" in name_lower or "floor" in name_lower:
            return RoundingTag.DOWN
        elif "up" in name_lower or "ceil" in name_lower:
            return RoundingTag.UP
        else:
            return RoundingTag.UNKNOWN

    def _get_variable_tag(
        self, var: Union[Variable, Constant], domain: RoundingDomain
    ) -> RoundingTag:
        """Get the rounding tag for a variable or constant"""
        if isinstance(var, Constant):
            # Constants are UNKNOWN by default
            return RoundingTag.UNKNOWN
        if isinstance(var, Variable):
            return domain.state.get_tag(var)
        return RoundingTag.UNKNOWN

    def _combine_tags(self, tag1: RoundingTag, tag2: RoundingTag) -> RoundingTag:
        """
        Combine two rounding tags.
        - If both are the same → preserve that tag
        - If one is UNKNOWN → preserve the other
        - If they differ → return UNKNOWN
        """
        if tag1 == tag2:
            return tag1
        if tag1 == RoundingTag.UNKNOWN:
            return tag2
        if tag2 == RoundingTag.UNKNOWN:
            return tag1
        # Different tags (e.g., UP vs DOWN) → UNKNOWN
        return RoundingTag.UNKNOWN
