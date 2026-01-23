"""Rounding analysis for Slither data-flow"""

from typing import List, Optional, Union, cast

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.logger import get_logger
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.library_call import LibraryCall
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.return_operation import Return
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant


class RoundingAnalysis(Analysis):
    """Analysis that tracks rounding direction metadata through data flow"""

    def __init__(self) -> None:
        self._direction: Direction = Forward()
        self._logger = get_logger(enable_ipython_embed=False, log_level="ERROR")
        self.inconsistencies: List[str] = []

    def domain(self) -> Domain:
        return RoundingDomain.bottom()

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return RoundingDomain.bottom()

    def transfer_function(self, node: Node, domain: Domain, operation: Optional[Operation]) -> None:
        """Core analysis logic - tag operations and propagate rounding metadata"""
        # Cast to RoundingDomain for type checking
        domain = cast(RoundingDomain, domain)

        if domain.variant == DomainVariant.BOTTOM:
            domain.variant = DomainVariant.STATE
            domain.state = RoundingState()

        if operation is None:
            return

        self._analyze_operation_by_type(operation, domain, node)

    def _analyze_operation_by_type(
        self, operation: Operation, domain: RoundingDomain, node: Node
    ) -> None:
        """Route operation to appropriate handler"""
        if isinstance(operation, Binary):
            self._handle_binary_operation(operation, domain, node)
        elif isinstance(operation, Assignment):
            self._handle_assignment_operation(operation, domain)
        elif isinstance(operation, (InternalCall, HighLevelCall, LibraryCall)):
            self._handle_function_call(operation, domain, node)
        elif isinstance(operation, Return):
            # Return operations don't change rounding tags, just propagate
            pass

    def _handle_binary_operation(
        self, operation: Binary, domain: RoundingDomain, node: Node
    ) -> None:
        """Handle arithmetic binary operations with inversion rules.

        Rules implemented:
        - A + B => rounding(A) (no rounding change)
        - A - B => inverted rounding(B)
        - A * B => rounding(A) (no rounding change)
        - A / B => inverted rounding(B)
        """
        if not operation.lvalue:
            return

        result_var = operation.lvalue
        left_var = operation.variable_left
        right_var = operation.variable_right
        op_type = operation.type

        # Helper to get tags (using existing helper)
        left_tag = self._get_variable_tag(left_var, domain)
        right_tag = self._get_variable_tag(right_var, domain)

        if op_type == BinaryType.DIVISION:
            # Check for ceiling division pattern: (a + b - 1) / b
            # This is a common idiom that effectively rounds UP
            is_ceiling_pattern = self._is_ceiling_division_pattern(left_var, right_var, domain)

            # Enforce denominator/numerator consistency before computing result tag.
            self._check_division_consistency(left_tag, right_tag, operation, node)

            if is_ceiling_pattern:
                # This is the (numerator + divisor - 1) / divisor pattern → tag as UP
                domain.state.set_tag(result_var, RoundingTag.UP, operation)
            else:
                # Standard division: default DOWN when denominator is neutral.
                if right_tag == RoundingTag.NEUTRAL:
                    domain.state.set_tag(result_var, RoundingTag.DOWN, operation)
                else:
                    # Standard division: result uses inverted denominator rounding
                    right_tag_inv = self._invert_tag(right_tag)
                    domain.state.set_tag(result_var, right_tag_inv, operation)
            return

        elif op_type == BinaryType.SUBTRACTION:
            # The subtracted element's rounding is inverted
            right_tag_inv = self._invert_tag(right_tag)
            domain.state.set_tag(result_var, right_tag_inv, operation)
            return

        elif op_type == BinaryType.ADDITION:
            # No rounding change for addition; keep left operand rounding
            domain.state.set_tag(result_var, left_tag, operation)
            return

        elif op_type == BinaryType.MULTIPLICATION:
            # No rounding change for multiplication; keep left operand rounding
            domain.state.set_tag(result_var, left_tag, operation)
            return

        elif op_type == BinaryType.POWER:
            # Exponentiation handling is disabled until explicit rounding rules are defined.
            self._logger.warning("Rounding for POWER is not implemented yet")
            return

    def _is_ceiling_division_pattern(
        self,
        dividend: Union[RVALUE, Function],
        divisor: Union[RVALUE, Function],
        domain: RoundingDomain,
    ) -> bool:
        """Detect the ceiling division pattern: (a + b - 1) / b

        This checks if:
        - dividend is the result of subtracting 1 from something
        - that something is the result of adding dividend's original value to divisor

        Returns True if the pattern matches, False otherwise.
        """
        if not isinstance(dividend, Variable):
            return False

        # Get the operation that produced the dividend
        sub_op = domain.state.get_producer(dividend)
        if not isinstance(sub_op, Binary) or sub_op.type != BinaryType.SUBTRACTION:
            return False

        # Check if subtracting 1
        if not isinstance(sub_op.variable_right, Constant):
            return False
        try:
            if int(sub_op.variable_right.value) != 1:
                return False
        except (ValueError, TypeError, AttributeError):
            return False

        # Get the left operand of the subtraction (should be an addition)
        add_result = sub_op.variable_left
        if not isinstance(add_result, Variable):
            return False

        add_op = domain.state.get_producer(add_result)
        if not isinstance(add_op, Binary) or add_op.type != BinaryType.ADDITION:
            return False

        # Check if one of the addition operands is the divisor
        divisor_name = divisor.name if isinstance(divisor, Variable) else str(divisor)
        left_name = (
            add_op.variable_left.name
            if isinstance(add_op.variable_left, Variable)
            else str(add_op.variable_left)
        )
        right_name = (
            add_op.variable_right.name
            if isinstance(add_op.variable_right, Variable)
            else str(add_op.variable_right)
        )

        return divisor_name == left_name or divisor_name == right_name

    def _handle_assignment_operation(self, operation: Assignment, domain: RoundingDomain) -> None:
        """Handle assignment: propagate tag from right side to left side"""
        if not operation.lvalue:
            return

        rvalue = operation.rvalue
        if isinstance(rvalue, Variable):
            tag = self._get_variable_tag(rvalue, domain)
            domain.state.set_tag(operation.lvalue, tag, operation)
        # For non-variable rvalues (functions, tuples), leave as UNKNOWN

    def _handle_function_call(
        self,
        operation: Union[InternalCall, HighLevelCall, LibraryCall],
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Handle function calls - infer rounding from function name"""
        if not operation.lvalue:
            return

        # Get function name
        func_name: str
        if isinstance(operation, InternalCall):
            if operation.function:
                func_name = operation.function.name
            else:
                func_name = str(operation.function_name)
        elif isinstance(operation, (HighLevelCall, LibraryCall)):
            func_name = str(operation.function_name.value)

        # Apply division consistency check for named divUp/divDown helpers.
        if self._is_named_division_function(func_name):
            # Ensure numerator/denominator ordering before enforcing the rule.
            self._check_named_division_consistency(operation, domain, node)

        # Infer tag from function name
        tag = self._infer_tag_from_name(func_name)
        domain.state.set_tag(operation.lvalue, tag, operation)

    def _infer_tag_from_name(self, function_name: Optional[object]) -> RoundingTag:
        """
        Infer rounding direction from function name.
        Accepts non-string inputs and coerces to string for name checks.
        """
        name_lower = str(function_name).lower() if function_name is not None else ""
        if "down" in name_lower or "floor" in name_lower:
            return RoundingTag.DOWN
        elif "up" in name_lower or "ceil" in name_lower:
            return RoundingTag.UP
        else:
            return RoundingTag.NEUTRAL

    def _is_named_division_function(self, function_name: str) -> bool:
        """Return True when function name indicates divUp/divDown helpers."""
        name_lower = function_name.lower()
        # Only match the specific helper names to avoid false positives.
        return "divup" in name_lower or "divdown" in name_lower

    def _check_named_division_consistency(
        self,
        operation: Union[InternalCall, HighLevelCall, LibraryCall],
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Enforce division consistency for divUp/divDown call arguments."""
        # Ensure we have both numerator and denominator arguments.
        if len(operation.arguments) < 2:
            return

        numerator = operation.arguments[0]
        denominator = operation.arguments[1]
        numerator_tag = self._get_variable_tag(numerator, domain)
        denominator_tag = self._get_variable_tag(denominator, domain)
        self._check_division_consistency(numerator_tag, denominator_tag, operation, node)

    def _get_variable_tag(
        self, var: Optional[Union[RVALUE, Function]], domain: RoundingDomain
    ) -> RoundingTag:
        """Get the rounding tag for a variable or constant.

        Accepts RVALUE/None and returns NEUTRAL for constants or unrecognized types.
        """
        if isinstance(var, Constant):
            # Constants are NEUTRAL by default
            return RoundingTag.NEUTRAL
        if isinstance(var, Variable):
            return domain.state.get_tag(var)
        # If var is none or other types (Function, RVALUE variants...), return NEUTRAL
        return RoundingTag.NEUTRAL

    def _invert_tag(self, tag: RoundingTag) -> RoundingTag:
        """Invert rounding direction (UP <-> DOWN) and keep neutral tags unchanged."""
        # Flip UP to DOWN to model inversion rules.
        if tag == RoundingTag.UP:
            return RoundingTag.DOWN
        # Flip DOWN to UP to model inversion rules.
        if tag == RoundingTag.DOWN:
            return RoundingTag.UP
        # Keep NEUTRAL/UNKNOWN as-is to avoid over-precision.
        return tag

    def _check_division_consistency(
        self,
        numerator_tag: RoundingTag,
        denominator_tag: RoundingTag,
        operation: Operation,
        node: Node,
    ) -> None:
        """Check numerator/denominator consistency for division operations."""
        # Only enforce the constraint when the denominator is non-neutral.
        if denominator_tag == RoundingTag.NEUTRAL:
            return

        # Numerator must be opposite or neutral; same non-neutral is inconsistent.
        if numerator_tag == denominator_tag:
            function_name = node.function.name
            message = (
                "Division rounding inconsistency in "
                f"{function_name}: numerator and denominator both "
                f"{numerator_tag.name} in {operation}"
            )
            self.inconsistencies.append(message)
            self._logger.error(message)
