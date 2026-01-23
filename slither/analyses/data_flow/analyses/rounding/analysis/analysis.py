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
from slither.core.cfg.node import Node, NodeType
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
        self.annotation_mismatches: List[str] = []

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
            # Initialize the domain state the first time we visit this path.
            domain.variant = DomainVariant.STATE
            domain.state = RoundingState()

        # Initialize tags for entry nodes so arguments/returns are NEUTRAL up front.
        self._initialize_entry_state(node, domain)

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
            self._handle_assignment_operation(operation, domain, node)
        elif isinstance(operation, (InternalCall, HighLevelCall, LibraryCall)):
            self._handle_function_call(operation, domain, node)
        elif isinstance(operation, Return):
            # Return operations don't change rounding tags, just propagate
            self._check_return_annotations(operation, domain, node)

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
            inconsistency_reason = self._check_division_consistency(
                left_tag, right_tag, operation, node
            )
            if inconsistency_reason:
                # Mark the result as UNKNOWN to surface inconsistent division usage.
                self._set_tag_with_annotation(
                    result_var,
                    RoundingTag.UNKNOWN,
                    operation,
                    node,
                    domain,
                    unknown_reason=inconsistency_reason,
                )
                return

            if is_ceiling_pattern:
                # This is the (numerator + divisor - 1) / divisor pattern → tag as UP
                self._set_tag_with_annotation(result_var, RoundingTag.UP, operation, node, domain)
            else:
                # Standard division: default DOWN when denominator is neutral.
                if right_tag == RoundingTag.NEUTRAL:
                    self._set_tag_with_annotation(
                        result_var, RoundingTag.DOWN, operation, node, domain
                    )
                else:
                    # Standard division: result uses inverted denominator rounding
                    right_tag_inv = self._invert_tag(right_tag)
                    self._set_tag_with_annotation(
                        result_var, right_tag_inv, operation, node, domain
                    )
            return

        elif op_type == BinaryType.SUBTRACTION:
            # The subtracted element's rounding is inverted
            right_tag_inv = self._invert_tag(right_tag)
            self._set_tag_with_annotation(result_var, right_tag_inv, operation, node, domain)
            return

        elif op_type == BinaryType.ADDITION:
            # For addition: if left is NEUTRAL, use right; otherwise use left
            result_tag = right_tag if left_tag == RoundingTag.NEUTRAL else left_tag
            self._set_tag_with_annotation(result_var, result_tag, operation, node, domain)
            return

        elif op_type == BinaryType.MULTIPLICATION:
            # For multiplication: if left is NEUTRAL, use right; otherwise use left
            result_tag = right_tag if left_tag == RoundingTag.NEUTRAL else left_tag
            self._set_tag_with_annotation(result_var, result_tag, operation, node, domain)
            return

        elif op_type == BinaryType.POWER:
            # Exponentiation handling is disabled until explicit rounding rules are defined.
            self._logger.warning("Rounding for POWER is not implemented yet")
            return

    def _initialize_entry_state(self, node: Node, domain: RoundingDomain) -> None:
        """Initialize entry-point variables to NEUTRAL for consistent tag display."""
        # Only initialize on entry nodes to avoid clobbering inferred tags.
        if node.type not in (NodeType.ENTRYPOINT, NodeType.OTHER_ENTRYPOINT):
            return
        # Ensure we have a function context before accessing parameters/returns.
        function = node.function
        if function is None:
            return
        # Seed state variables as NEUTRAL so contract fields display tags.
        contract = function.contract
        if contract is not None:
            for state_var in contract.state_variables:
                # Mark state variables NEUTRAL to show tags in outputs.
                domain.state.set_tag(state_var, RoundingTag.NEUTRAL)
        # Seed parameters as NEUTRAL to show argument tags immediately.
        for param in function.parameters:
            # Mark parameters NEUTRAL so usage shows tags in operations.
            domain.state.set_tag(param, RoundingTag.NEUTRAL)
        # Seed return variables as NEUTRAL to show return tags even before assignment.
        for return_var in function.returns:
            # Mark return variables NEUTRAL to show tags in outputs.
            domain.state.set_tag(return_var, RoundingTag.NEUTRAL)

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

    def _handle_assignment_operation(
        self, operation: Assignment, domain: RoundingDomain, node: Node
    ) -> None:
        """Handle assignment: propagate tag from right side to left side"""
        if not operation.lvalue:
            return

        rvalue = operation.rvalue
        if isinstance(rvalue, Variable):
            tag = self._get_variable_tag(rvalue, domain)
            self._set_tag_with_annotation(operation.lvalue, tag, operation, node, domain)
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
        self._set_tag_with_annotation(operation.lvalue, tag, operation, node, domain)

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
        inconsistency_reason = self._check_division_consistency(
            numerator_tag, denominator_tag, operation, node
        )
        if inconsistency_reason and operation.lvalue:
            # Mark the call result as UNKNOWN for inconsistent divisions.
            self._set_tag_with_annotation(
                operation.lvalue,
                RoundingTag.UNKNOWN,
                operation,
                node,
                domain,
                unknown_reason=inconsistency_reason,
            )

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

    def _set_tag_with_annotation(
        self,
        var: Variable,
        tag: RoundingTag,
        operation: Operation,
        node: Node,
        domain: RoundingDomain,
        unknown_reason: Optional[str] = None,
    ) -> None:
        """Set a tag and enforce any annotation-based expectations."""
        domain.state.set_tag(var, tag, operation, unknown_reason=unknown_reason)
        self._check_annotation_for_variable(var, tag, operation, node, domain)

    def _check_return_annotations(
        self, operation: Return, domain: RoundingDomain, node: Node
    ) -> None:
        """Check annotations on return variables for mismatched rounding."""
        # Iterate return values to validate any annotated variables.
        for return_value in operation.values:
            # Skip non-variable return values because only variables can be annotated.
            if not isinstance(return_value, Variable):
                continue
            return_tag = domain.state.get_tag(return_value)
            self._check_annotation_for_variable(return_value, return_tag, operation, node, domain)

    def _check_annotation_for_variable(
        self,
        var: Variable,
        actual_tag: RoundingTag,
        operation: Operation,
        node: Node,
        domain: RoundingDomain,
    ) -> None:
        """Validate variable annotation suffixes against inferred rounding."""
        expected_tag = self._parse_expected_tag_from_name(var.name)
        # Skip variables without annotation suffixes to avoid noisy reporting.
        if expected_tag is None:
            return
        # Report when the inferred tag does not match the developer annotation.
        if actual_tag != expected_tag:
            function_name = node.function.name
            unknown_reason = domain.state.get_unknown_reason(var)
            reason_suffix = f" ({unknown_reason})" if unknown_reason else ""
            message = (
                "Rounding annotation mismatch in "
                f"{function_name}: {var.name} expected "
                f"{expected_tag.name} but inferred {actual_tag.name}"
                f"{reason_suffix} in {operation}"
            )
            self.annotation_mismatches.append(message)
            self._logger.error(message)

    def _parse_expected_tag_from_name(self, name: str) -> Optional[RoundingTag]:
        """Parse annotation suffixes like _UP/_DOWN/_NEUTRAL from variable names."""
        name_upper = name.upper()
        suffix_to_tag = (
            ("_UP", RoundingTag.UP),
            ("_DOWN", RoundingTag.DOWN),
            ("_NEUTRAL", RoundingTag.NEUTRAL),
        )
        # Scan for suffix annotations so we only enforce explicit expectations.
        for suffix, tag in suffix_to_tag:
            # Treat suffix matches as rounding annotations to validate against.
            if name_upper.endswith(suffix):
                return tag
        return None

    def _check_division_consistency(
        self,
        numerator_tag: RoundingTag,
        denominator_tag: RoundingTag,
        operation: Operation,
        node: Node,
    ) -> Optional[str]:
        """Check numerator/denominator consistency for division operations."""
        # Only enforce the constraint when the denominator is non-neutral.
        if denominator_tag == RoundingTag.NEUTRAL:
            return None

        # Numerator must be opposite or neutral; same non-neutral is inconsistent.
        if numerator_tag == denominator_tag:
            function_name = node.function.name
            # Provide a reason string for UNKNOWN tagging on inconsistent division.
            reason = (
                "Inconsistent division: numerator and denominator both "
                f"{numerator_tag.name} in {function_name}"
            )
            message = (
                "Division rounding inconsistency in "
                f"{function_name}: numerator and denominator both "
                f"{numerator_tag.name} in {operation}"
            )
            self.inconsistencies.append(message)
            self._logger.error(message)
            return reason
        return None
