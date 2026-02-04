"""Addition operation handler for rounding analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class AdditionHandler(BinaryOperationHandler):
    """Handler for addition: A + B => rounding(A) or rounding(B) if A is NEUTRAL."""

    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
    ) -> None:
        """Handle addition by preserving the non-neutral operand's tag."""
        result_variable = operation.lvalue
        result_tag = right_tag if left_tag == RoundingTag.NEUTRAL else left_tag
        self.set_tag_with_annotation(
            result_variable, result_tag, operation, node, domain
        )
