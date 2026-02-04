"""Division operation handler for rounding analysis.

Rule from roundme: A / B => rounding(A), !rounding(B), rounding(/)
Numerator preserves direction, denominator's direction is inverted.
Floor division is the default when both operands are NEUTRAL.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    combine_tags,
    invert_tag,
)
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class DivisionHandler(BinaryOperationHandler):
    """Handler for division: A / B => rounding(A), !rounding(B), rounding(/).

    Numerator preserves direction, denominator's direction is inverted.
    Floor division (DOWN) is the default when both operands are NEUTRAL.
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
        result_variable = operation.lvalue

        # Check for ceiling division pattern first
        is_ceiling = self._is_ceiling_division_pattern(
            operation.variable_left, operation.variable_right, domain
        )
        if is_ceiling:
            self.set_tag_with_annotation(
                result_variable, RoundingTag.UP, operation, node, domain
            )
            return

        # Check for legacy inconsistency (numerator and denominator same non-NEUTRAL)
        inconsistency = self._check_division_consistency(
            left_tag, right_tag, operation, node
        )
        if inconsistency:
            self.set_tag_with_annotation(
                result_variable, RoundingTag.UNKNOWN, operation, node, domain,
                unknown_reason=inconsistency,
            )
            return

        # Combine numerator with inverted denominator per roundme rules
        right_tag_inverted = invert_tag(right_tag)
        result_tag, has_conflict = combine_tags(left_tag, right_tag_inverted)

        if has_conflict:
            reason = self._format_conflict_reason(
                left_tag, right_tag, right_tag_inverted, node
            )
            self.set_tag_with_annotation(
                result_variable, RoundingTag.UNKNOWN, operation, node, domain,
                unknown_reason=reason,
            )
            return

        # Default to floor division when both operands are NEUTRAL
        if result_tag == RoundingTag.NEUTRAL:
            result_tag = RoundingTag.DOWN

        self.set_tag_with_annotation(
            result_variable, result_tag, operation, node, domain
        )

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
        self.analysis.inconsistencies.append(message)
        self.analysis._logger.error(message)
        return message

    def _is_ceiling_division_pattern(
        self,
        dividend: Union[RVALUE, Function],
        divisor: Union[RVALUE, Function],
        domain: "RoundingDomain",
    ) -> bool:
        """Detect the ceiling division pattern: (a + b - 1) / b."""
        if not isinstance(dividend, Variable):
            return False

        addition_result = self._check_subtraction_minus_one(dividend, domain)
        if addition_result is None:
            return False

        return self._check_addition_includes_divisor(addition_result, divisor, domain)

    def _check_subtraction_minus_one(
        self, variable: Variable, domain: "RoundingDomain"
    ) -> Optional[Variable]:
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
            return False

    def _check_addition_includes_divisor(
        self,
        addition_result: Variable,
        divisor: Union[RVALUE, Function],
        domain: "RoundingDomain",
    ) -> bool:
        """Check if addition_result was produced by addition including divisor."""
        addition_operation = domain.state.get_producer(addition_result)
        if not isinstance(addition_operation, Binary):
            return False
        if addition_operation.type != BinaryType.ADDITION:
            return False

        divisor_name = divisor.name if isinstance(divisor, Variable) else str(divisor)
        left_name = self._get_operand_name(addition_operation.variable_left)
        right_name = self._get_operand_name(addition_operation.variable_right)

        return divisor_name == left_name or divisor_name == right_name

    def _get_operand_name(self, operand: Union[RVALUE, Function]) -> str:
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
    ) -> Optional[str]:
        """Check numerator/denominator consistency for division operations."""
        if denominator_tag == RoundingTag.NEUTRAL:
            return None

        if numerator_tag == denominator_tag:
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
            self.analysis.inconsistencies.append(message)
            self.analysis._logger.error(message)
            return reason
        return None
