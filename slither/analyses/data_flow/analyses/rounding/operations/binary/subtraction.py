"""Subtraction operation handler for rounding analysis.

Rule from roundme: A - B => rounding(A), !rounding(B)
The minuend preserves direction, the subtrahend's direction is inverted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    combine_tags,
    invert_tag,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class SubtractionHandler(BinaryOperationHandler):
    """Handler for subtraction: A - B => rounding(A), !rounding(B).

    The minuend (A) preserves its rounding direction, while the subtrahend (B)
    has its direction inverted. Both must agree after inversion.
    """

    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
    ) -> None:
        """Handle subtraction by combining left with inverted right."""
        result_variable = operation.lvalue
        right_tag_inverted = invert_tag(right_tag)
        result_tag, has_conflict = combine_tags(left_tag, right_tag_inverted)

        if has_conflict:
            reason = self._format_conflict_reason(
                left_tag, right_tag, right_tag_inverted, node
            )
            self.set_tag_with_annotation(
                result_variable, result_tag, operation, node, domain,
                unknown_reason=reason,
            )
            return

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
            f"Conflicting rounding in subtraction: {left_tag.name} - {right_tag.name} "
            f"(inverted: {right_inverted.name}) in {function_name}"
        )
        self.analysis.inconsistencies.append(message)
        self.analysis._logger.error(message)
        return message
