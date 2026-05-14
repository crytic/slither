"""Main binary operation handler that dispatches to specific handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
    TagSet,
    TraceNode,
)
from slither.analyses.data_flow.analyses.rounding.core.models import RoundingFinding
from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.addition import (
    AdditionHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.base import (
    BinaryOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.division import (
    DivisionHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary import (
    multiplication,
)
from slither.analyses.data_flow.analyses.rounding.operations.binary.subtraction import (
    SubtractionHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    combine_tag_sets,
    combine_tags,
    get_variable_tags,
    invert_tag_set,
)
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary, BinaryType

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )

_INVERT_RIGHT_OPS: frozenset[BinaryType] = frozenset({
    BinaryType.SUBTRACTION,
    BinaryType.DIVISION,
})

_OP_SYMBOL: dict[BinaryType, str] = {
    BinaryType.ADDITION: "+",
    BinaryType.SUBTRACTION: "-",
    BinaryType.MULTIPLICATION: "*",
    BinaryType.DIVISION: "/",
}

_ROUNDING_IRRELEVANT_OPS: frozenset[BinaryType] = frozenset({
    BinaryType.LEFT_SHIFT,
    BinaryType.RIGHT_SHIFT,
    BinaryType.AND,
    BinaryType.CARET,
    BinaryType.OR,
    BinaryType.LESS,
    BinaryType.GREATER,
    BinaryType.LESS_EQUAL,
    BinaryType.GREATER_EQUAL,
    BinaryType.EQUAL,
    BinaryType.NOT_EQUAL,
    BinaryType.ANDAND,
    BinaryType.OROR,
    BinaryType.MODULO,
})


class BinaryHandler(BaseOperationHandler):
    """Handler for binary operations - dispatches to type-specific handlers."""

    def __init__(self, analysis: "RoundingAnalysis") -> None:
        super().__init__(analysis)
        self._handlers: dict[BinaryType, BinaryOperationHandler] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register handlers for each binary operation type."""
        self._handlers[BinaryType.DIVISION] = DivisionHandler(self._analysis)
        self._handlers[BinaryType.SUBTRACTION] = SubtractionHandler(self._analysis)
        self._handlers[BinaryType.ADDITION] = AdditionHandler(self._analysis)
        multiplication_handler = multiplication.MultiplicationHandler(self._analysis)
        self._handlers[BinaryType.MULTIPLICATION] = multiplication_handler

    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
    ) -> None:
        """Process binary operation by dispatching to appropriate handler."""
        if not operation.lvalue:
            return

        operation_type = operation.type
        if operation_type in _ROUNDING_IRRELEVANT_OPS:
            return

        left_tags = get_variable_tags(operation.variable_left, domain)
        right_tags = get_variable_tags(operation.variable_right, domain)

        if len(left_tags) == 1 and len(right_tags) == 1:
            handler = self._handlers.get(operation_type)
            if handler is not None:
                left_tag = next(iter(left_tags))
                right_tag = next(iter(right_tags))
                handler.handle(operation, domain, node, left_tag, right_tag)
                return
            self.analysis._logger.warning(
                "No rounding handler for binary op {op}",
                op=operation_type.name,
            )
            return

        if operation_type not in self._handlers:
            return

        self._handle_multi_tag(
            operation, domain, node, left_tags, right_tags, operation_type,
        )

    def _handle_multi_tag(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
        left_tags: TagSet,
        right_tags: TagSet,
        operation_type: BinaryType,
    ) -> None:
        """Handle a binary op where at least one operand carries multiple tags.

        Computes the cross-product of `combine_tags(l, r)` over every pair,
        applying inversion to the right operand for SUB/DIV. Only flags an
        inconsistency if *every* pair conflicts. Floor bias and ceiling
        pattern detection are skipped here because those single-tag
        heuristics do not apply to branched provenance.
        """
        right_for_combine = (
            invert_tag_set(right_tags)
            if operation_type in _INVERT_RIGHT_OPS
            else right_tags
        )
        result_set, every_pair_conflicts = _combine_pairwise(
            left_tags, right_for_combine
        )

        op_symbol = _OP_SYMBOL.get(operation_type, "?")
        source = (
            f"{_format_tagset(left_tags)} {op_symbol} "
            f"{_format_tagset(right_tags)} → {_format_tagset(result_set)}"
        )
        trace = TraceNode(
            function_name=node.function.name,
            line_number=node.source_mapping.lines[0]
            if node.source_mapping and node.source_mapping.lines
            else None,
            tags=result_set,
            source=source,
            children=[],
        )

        unknown_reason: str | None = None
        if every_pair_conflicts and result_set == frozenset({RoundingTag.UNKNOWN}):
            unknown_reason = self._record_multi_tag_conflict(
                operation_type, left_tags, right_tags, node,
            )

        domain.state.set_tag(
            operation.lvalue, result_set, operation,
            unknown_reason=unknown_reason, trace=trace,
        )
        self.analysis._check_annotation_for_variable(
            operation.lvalue, domain.state.get_tag(operation.lvalue),
            operation, node, domain,
        )

    def _record_multi_tag_conflict(
        self,
        operation_type: BinaryType,
        left_tags: TagSet,
        right_tags: TagSet,
        node: Node,
    ) -> str:
        """Record an inconsistency when every multi-tag combination conflicts."""
        op_name = operation_type.name.lower()
        function_name = node.function.name
        message = (
            f"Conflicting rounding in {op_name}: "
            f"{_format_tagset(left_tags)} {_OP_SYMBOL.get(operation_type, '?')} "
            f"{_format_tagset(right_tags)} in {function_name}"
        )
        self.analysis.record_inconsistency(
            RoundingFinding(message=message, node=node)
        )
        self.analysis._logger.warning(message)
        return message


def _combine_pairwise(
    left_tags: TagSet,
    right_tags: TagSet,
) -> tuple[TagSet, bool]:
    """Cross-combine two tag sets. Returns (result, every_pair_conflicted)."""
    result_set, _ = combine_tag_sets(left_tags, right_tags)
    all_conflict = True
    for left_tag in left_tags:
        for right_tag in right_tags:
            _, conflict = combine_tags(left_tag, right_tag)
            if not conflict:
                all_conflict = False
                break
        if not all_conflict:
            break
    return result_set, all_conflict


def _format_tagset(tags: TagSet) -> str:
    if len(tags) == 1:
        return next(iter(tags)).name
    return "{" + ", ".join(sorted(tag.name for tag in tags)) + "}"


# Import here to avoid circular import at module level
if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )
