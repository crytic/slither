"""Shared dataclasses for rounding analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from slither.analyses.data_flow.analyses.rounding.core.state import (
    TagSet,
    TraceNode,
)
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable


@dataclass
class RoundingFinding:
    """A structured finding with node reference for detector output."""

    message: str
    node: Node | None
    variable: Variable | None = None


@dataclass(frozen=True)
class RoundingCallSummary:
    """Summary of a callee's return values for one call site.

    Produced by ``RoundingAnalysis.extract_return_summary`` after a
    nested fixpoint over the callee, or by ``on_recursion`` when the
    callee's analysis was skipped.

    Attributes:
        tags: Union of scalar return tags across all Return nodes
            (first return value only), or None when no return tags
            were found.
        traces: Provenance traces for the scalar return values.
        per_index: Per-return-index (tags, traces) pairs from the first
            Return node, used by tuple-returning call sites.
        from_recursion: True when the summary stands in for a skipped
            (recursive or depth-capped) analysis; tuple call sites
            treat such summaries as a silent no-op instead of raising
            on the empty ``per_index``.
    """

    tags: TagSet | None
    traces: list[TraceNode]
    per_index: list[tuple[TagSet, list[TraceNode]]]
    from_recursion: bool = False


@dataclass
class LineAnnotation:
    """Annotation for a single variable on a source line."""

    variable_name: str
    tags: TagSet
    is_return: bool = False
    note: str = ""


@dataclass
class AnnotatedLine:
    """Source line with its annotations."""

    line_number: int
    source_text: str
    annotations: list[LineAnnotation] = field(default_factory=list)
    is_entry: bool = False


@dataclass
class AnnotatedFunction:
    """Complete annotated source view for a function."""

    function_name: str
    contract_name: str
    filename: str
    start_line: int
    end_line: int
    lines: dict[int, AnnotatedLine] = field(default_factory=dict)
    return_tags: dict[str, TagSet] = field(default_factory=dict)
    inconsistencies: list[RoundingFinding] = field(default_factory=list)
    annotation_mismatches: list[RoundingFinding] = field(default_factory=list)
    traces: dict[str, TraceNode] = field(default_factory=dict)
    node_results: dict[Node, AnalysisState] = field(default_factory=dict)


def get_node_line(node: Node | None) -> int | None:
    """Get the primary source line for a node, or None if node is missing."""
    if node is None:
        return None
    if node.source_mapping and node.source_mapping.lines:
        return node.source_mapping.lines[0]
    return None
