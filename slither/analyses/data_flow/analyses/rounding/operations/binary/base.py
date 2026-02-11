"""Base class for binary operation handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
    TraceNode,
)
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )


class BinaryOperationHandler(ABC):
    """Abstract base class for binary operation type handlers."""

    def __init__(self, analysis: "RoundingAnalysis"):
        self._analysis = analysis

    @property
    def analysis(self) -> "RoundingAnalysis":
        """Return the analysis instance."""
        return self._analysis

    @abstractmethod
    def handle(
        self,
        operation: Binary,
        domain: "RoundingDomain",
        node: Node,
        left_tag: RoundingTag,
        right_tag: RoundingTag,
    ) -> None:
        """Process the binary operation."""

    def set_tag_with_annotation(
        self,
        variable: Variable,
        tag: RoundingTag,
        operation: Binary,
        node: Node,
        domain: "RoundingDomain",
        unknown_reason: Optional[str] = None,
        trace: Optional[TraceNode] = None,
    ) -> None:
        """Set a tag and enforce any annotation-based expectations."""
        domain.state.set_tag(
            variable, tag, operation,
            unknown_reason=unknown_reason,
            trace=trace,
        )
        self._analysis._check_annotation_for_variable(
            variable, tag, operation, node, domain
        )

    def _build_binary_trace(
        self,
        node: Node,
        operation: Binary,
        domain: "RoundingDomain",
        result_tag: RoundingTag,
        source: str,
    ) -> TraceNode:
        """Build a TraceNode for a binary operation result."""
        line_number = (
            node.source_mapping.lines[0]
            if node.source_mapping
            else None
        )
        children = self._collect_operand_traces(operation, domain)
        return TraceNode(
            function_name=node.function.name,
            line_number=line_number,
            tags=frozenset({result_tag}),
            source=source,
            children=children,
        )

    def _collect_operand_traces(
        self,
        operation: Binary,
        domain: "RoundingDomain",
    ) -> list[TraceNode]:
        """Collect existing traces from binary operands."""
        children: list[TraceNode] = []
        for operand in [operation.variable_left, operation.variable_right]:
            if not isinstance(operand, Variable):
                continue
            operand_trace = domain.state.get_trace(operand)
            if operand_trace is not None:
                children.append(operand_trace)
        return children
