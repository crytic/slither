"""Multiplication operation handler for rounding analysis.

Rule from roundme: A * B => rounding(A), rounding(B), rounding(*)
Both operands must agree on rounding direction for the result to be well-defined.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    combine_tags,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class MultiplicationHandler(BinaryOperationHandler):
    """Handler for multiplication: A * B => rounding(A), rounding(B).

    Both operands propagate their rounding direction. If they conflict (UP * DOWN),
    the result is UNKNOWN and flagged as inconsistent.
    """

    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
    ) -> None:
        """Handle multiplication by combining both operands' tags."""
        result_variable = operation.lvalue
        result_tag, has_conflict = combine_tags(left_tag, right_tag)

        if has_conflict:
            reason = self._format_conflict_reason(left_tag, right_tag, node)
            self.set_tag_with_annotation(
                result_variable, result_tag, operation, node, domain,
                unknown_reason=reason,
            )
            return

        self.set_tag_with_annotation(
            result_variable, result_tag, operation, node, domain
        )

    def _format_conflict_reason(
        self, left_tag: RoundingTag, right_tag: RoundingTag, node: Node
    ) -> str:
        """Format a human-readable conflict reason."""
        function_name = node.function.name
        message = (
            f"Conflicting rounding in multiplication: "
            f"{left_tag.name} * {right_tag.name} in {function_name}"
        )
        self.analysis.inconsistencies.append(message)
        self.analysis._logger.error(message)
        return message
