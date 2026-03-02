"""Division operation handler for rounding analysis.

Rule from roundme: A / B => rounding(A), !rounding(B), rounding(/)
Numerator preserves direction, denominator's direction is inverted.
Floor division (DOWN) dominates when either operand is NEUTRAL — Solidity's
truncation bias overwhelms a single operand's rounding signal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.core.models import RoundingFinding
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    combine_tags,
    invert_tag,
)
from slither.analyses.data_flow.logger import get_logger
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant

_logger = get_logger()

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class DivisionHandler(BinaryOperationHandler):
    """Handler for division: A / B => rounding(A), !rounding(B), rounding(/).

    Numerator preserves direction, denominator's direction is inverted.
    Floor division (DOWN) dominates when either operand is NEUTRAL \u2014 Solidity's
    truncation bias overwhelms a single operand's rounding signal. When both
    operands have non-NEUTRAL tags that agree (after inversion), the operand
    signal is strong enough to override the floor bias.
    Ceiling division pattern (a + b - 1) / b is detected and tagged as UP.
    """

    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
    ) -> None:
        """Handle division with ceiling pattern detection and consistency checks."""
        if self._handle_ceiling_pattern(operation, domain, node):
            return

        if self._handle_consistency_error(
            left_tag, right_tag, operation, node, domain
        ):
            return

        self._handle_normal_division(
            left_tag, right_tag, operation, node, domain
        )

    def _handle_ceiling_pattern(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
    ) -> bool:
        """Detect and handle ceiling division pattern. Returns True if handled."""
        if not self._is_ceiling_division_pattern(
            operation.variable_left, operation.variable_right, domain
        ):
            return False
        trace = self._build_binary_trace(
            node, operation, domain,
            RoundingTag.UP, "ceiling division \u2192 UP",
        )
        self.set_tag_with_annotation(
            operation.lvalue, RoundingTag.UP, operation, node, domain,
            trace=trace,
        )
        return True

    def _handle_consistency_error(
        self,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
        operation: Binary,
        node: Node,
        domain: "RoundingDomain",
    ) -> bool:
        """Handle numerator/denominator consistency error. Returns True if handled."""
        inconsistency = self._check_division_consistency(
            left_tag, right_tag, operation, node
        )
        if not inconsistency:
            return False
        source = (
            f"{left_tag.name} / {right_tag.name} "
            f"(inconsistent) \u2192 UNKNOWN"
        )
        trace = self._build_binary_trace(
            node, operation, domain, RoundingTag.UNKNOWN, source,
        )
        self.set_tag_with_annotation(
            operation.lvalue, RoundingTag.UNKNOWN, operation, node, domain,
            unknown_reason=inconsistency, trace=trace,
        )
        return True

    def _handle_normal_division(
        self,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
        operation: Binary,
        node: Node,
        domain: "RoundingDomain",
    ) -> None:
        """Handle normal division with inversion and floor bias."""
        right_inverted = invert_tag(right_tag)
        result_tag, has_conflict = combine_tags(left_tag, right_inverted)

        if has_conflict:
            reason = self._format_conflict_reason(
                left_tag, right_tag, right_inverted, node
            )
            source = (
                f"{left_tag.name} / {right_tag.name} "
                f"(inverted: {right_inverted.name}) "
                f"conflict \u2192 UNKNOWN"
            )
            trace = self._build_binary_trace(
                node, operation, domain, RoundingTag.UNKNOWN, source,
            )
            self.set_tag_with_annotation(
                operation.lvalue, RoundingTag.UNKNOWN,
                operation, node, domain,
                unknown_reason=reason, trace=trace,
            )
            return

        either_neutral = (
            left_tag == RoundingTag.NEUTRAL
            or right_tag == RoundingTag.NEUTRAL
        )
        if either_neutral:
            result_tag = RoundingTag.DOWN

        source = self._format_division_source(
            left_tag, right_tag, right_inverted,
            result_tag, either_neutral,
        )
        trace = self._build_binary_trace(
            node, operation, domain, result_tag, source,
        )
        self.set_tag_with_annotation(
            operation.lvalue, result_tag, operation, node, domain,
            trace=trace,
        )

    def _format_division_source(
        self,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
        right_inverted: RoundingTag,
        result_tag: RoundingTag,
        floor_bias: bool,
    ) -> str:
        """Format trace source string for normal division."""
        base = (
            f"{left_tag.name} / {right_tag.name} "
            f"(inverted: {right_inverted.name})"
        )
        if floor_bias:
            return f"{base} floor bias \u2192 {result_tag.name}"
        return f"{base} \u2192 {result_tag.name}"

    def _format_conflict_reason(
        self,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
        right_inverted: RoundingTag,
        node: Node,
    ) -> str:
        """Format a human-readable conflict reason."""
        function_name = node.function.name
        message = (
            f"Conflicting rounding in division: {left_tag.name} / {right_tag.name} "
            f"(inverted: {right_inverted.name}) in {function_name}"
        )
        self.analysis.inconsistencies.append(
            RoundingFinding(message=message, node=node)
        )
        self.analysis._logger.warning(message)
        return message

    def _is_ceiling_division_pattern(
        self,
        dividend: RVALUE | Function,
        divisor: RVALUE | Function,
        domain: "RoundingDomain",
    ) -> bool:
        """Detect the ceiling division pattern: (a + b - 1) / b."""
        if not isinstance(dividend, Variable):
            _logger.debug("Ceiling check: dividend is not a Variable")
            return False

        addition_result = self._check_subtraction_minus_one(dividend, domain)
        if addition_result is None:
            _logger.debug("Ceiling check: dividend is not (X - 1)")
            return False

        if not self._check_addition_includes_divisor(
            addition_result, divisor, domain
        ):
            _logger.debug("Ceiling check: addition does not include divisor")
            return False

        return True

    def _check_subtraction_minus_one(
        self, variable: Variable, domain: "RoundingDomain"
    ) -> Variable | None:
        """Check if variable = X - 1 and return X, or None."""
        subtraction_operation = domain.state.get_producer(variable)
        if not isinstance(subtraction_operation, Binary):
            return None
        if subtraction_operation.type != BinaryType.SUBTRACTION:
            return None
        if not isinstance(subtraction_operation.variable_right, Constant):
            return None
        if not self._is_constant_one(subtraction_operation.variable_right):
            return None

        addition_result = subtraction_operation.variable_left
        if not isinstance(addition_result, Variable):
            return None
        return addition_result

    def _is_constant_one(self, constant: Constant) -> bool:
        """Check if a constant has value 1."""
        try:
            return int(constant.value) == 1
        except (ValueError, TypeError, AttributeError):
            _logger.debug(
                "Could not parse constant as int: {val}",
                val=constant.value,
            )
            return False

    def _check_addition_includes_divisor(
        self,
        addition_result: Variable,
        divisor: RVALUE | Function,
        domain: "RoundingDomain",
    ) -> bool:
        """Check if addition_result was produced by addition including divisor."""
        addition_operation = domain.state.get_producer(addition_result)
        if not isinstance(addition_operation, Binary):
            return False
        if addition_operation.type != BinaryType.ADDITION:
            return False

        divisor_name = (
            divisor.name if isinstance(divisor, Variable) else str(divisor)
        )
        left_name = self._get_operand_name(addition_operation.variable_left)
        right_name = self._get_operand_name(addition_operation.variable_right)

        return divisor_name == left_name or divisor_name == right_name

    def _get_operand_name(self, operand: RVALUE | Function) -> str:
        """Get the name of an operand."""
        if isinstance(operand, Variable):
            return operand.name
        return str(operand)

    def _check_division_consistency(
        self,
        numerator_tag: RoundingTag,
        denominator_tag: RoundingTag,
        operation: Binary,
        node: Node,
    ) -> str | None:
        """Check numerator/denominator consistency for division operations."""
        if denominator_tag == RoundingTag.NEUTRAL:
            return None

        if numerator_tag != denominator_tag:
            return None

        function_name = node.function.name
        reason = (
            "Inconsistent division: numerator and denominator both "
            f"{numerator_tag.name} in {function_name}"
        )
        message = (
            "Division rounding inconsistency in "
            f"{function_name}: numerator and denominator both "
            f"{numerator_tag.name} in {operation}"
        )
        self.analysis.inconsistencies.append(
            RoundingFinding(message=message, node=node)
        )
        self.analysis._logger.warning(message)
        return reason
