"""Subtraction operation handler for rounding analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    invert_tag,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class SubtractionHandler(BinaryOperationHandler):
    """Handler for subtraction: A - B => inverted rounding(B)."""

    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
    ) -> None:
        """Handle subtraction by inverting the right operand's tag."""
        result_variable = operation.lvalue
        right_tag_inverted = invert_tag(right_tag)
        self.set_tag_with_annotation(
            result_variable, right_tag_inverted, operation, node, domain
        )
