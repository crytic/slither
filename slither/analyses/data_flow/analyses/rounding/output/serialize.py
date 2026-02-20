"""Rounding-specific serialization for AnnotatedFunction results.

Converts rounding analysis IR objects to JSON-serializable TypedDicts.
Uses shared helpers from registry.serialization for Node/Variable
conversion, and adds rounding-specific structure (traces, findings,
line annotations, return tags).

The top-level ``RoundingResult`` TypedDict is the serialized form
consumed by slither-mcp and ``--json`` output.
"""

from __future__ import annotations

from typing import List, Optional, TypedDict

from slither.analyses.data_flow.analyses.rounding.core.state import (
    TraceNode,
)
from slither.analyses.data_flow.analyses.rounding.core.models import (
    AnnotatedFunction,
    AnnotatedLine,
    LineAnnotation,
    RoundingFinding,
    get_node_line,
)
from slither.analyses.data_flow.registry.serialization import (
    serialize_variable_ref,
)


# ── TypedDicts ───────────────────────────────────────────────────


class FindingDict(TypedDict):
    """Serialized RoundingFinding."""

    message: str
    line_number: Optional[int]
    variable_name: Optional[str]


class TraceNodeDict(TypedDict):
    """Serialized TraceNode provenance chain."""

    function_name: str
    line_number: Optional[int]
    tags: List[str]
    source: str
    children: List[TraceNodeDict]
    branch_condition: Optional[str]


class AnnotationDict(TypedDict):
    """Serialized LineAnnotation."""

    variable_name: str
    tags: List[str]
    is_return: bool
    note: str


class AnnotatedLineDict(TypedDict):
    """Serialized AnnotatedLine."""

    line_number: int
    source_text: str
    annotations: List[AnnotationDict]
    is_entry: bool


class RoundingResult(TypedDict):
    """Serialized AnnotatedFunction — the top-level result type.

    This is the ``T`` bound for ``RoundingCLI(AbstractAnalysis[T])``.
    """

    function_name: str
    contract_name: str
    filename: str
    start_line: int
    end_line: int
    lines: List[AnnotatedLineDict]
    return_tags: dict[str, List[str]]
    inconsistencies: List[FindingDict]
    annotation_mismatches: List[FindingDict]
    traces: dict[str, TraceNodeDict]


# ── Serialization functions ──────────────────────────────────────


def serialize_tag_set(tags: frozenset) -> List[str]:
    """Convert a TagSet to sorted name strings."""
    return sorted(tag.name for tag in tags)


def serialize_trace_node(
    trace: TraceNode,
    max_depth: int = 10,
) -> TraceNodeDict:
    """Recursively serialize a TraceNode provenance chain.

    Args:
        trace: The root TraceNode to serialize.
        max_depth: Maximum recursion depth to prevent runaway trees.

    Returns:
        A nested TraceNodeDict with all children serialized.
    """
    children: List[TraceNodeDict] = []
    if max_depth > 0:
        children = [
            serialize_trace_node(child, max_depth - 1)
            for child in trace.children
        ]

    return TraceNodeDict(
        function_name=trace.function_name,
        line_number=trace.line_number,
        tags=serialize_tag_set(trace.tags),
        source=trace.source,
        children=children,
        branch_condition=trace.branch_condition,
    )


def serialize_finding(finding: RoundingFinding) -> FindingDict:
    """Serialize a RoundingFinding to plain data.

    Args:
        finding: A RoundingFinding with Slither IR references.

    Returns:
        A FindingDict with line number and variable name extracted.
    """
    return FindingDict(
        message=finding.message,
        line_number=get_node_line(finding.node),
        variable_name=serialize_variable_ref(finding.variable),
    )


def serialize_annotation(annotation: LineAnnotation) -> AnnotationDict:
    """Serialize a LineAnnotation to plain data."""
    return AnnotationDict(
        variable_name=annotation.variable_name,
        tags=serialize_tag_set(annotation.tags),
        is_return=annotation.is_return,
        note=annotation.note,
    )


def serialize_line(line: AnnotatedLine) -> AnnotatedLineDict:
    """Serialize an AnnotatedLine to plain data."""
    return AnnotatedLineDict(
        line_number=line.line_number,
        source_text=line.source_text,
        annotations=[
            serialize_annotation(annotation)
            for annotation in line.annotations
        ],
        is_entry=line.is_entry,
    )


def serialize_annotated_function(
    annotated: AnnotatedFunction,
) -> RoundingResult:
    """Serialize an AnnotatedFunction to a JSON-serializable dict.

    Strips all Slither IR references (Node, Variable, AnalysisState)
    and produces a plain RoundingResult TypedDict suitable for JSON
    output and slither-mcp Pydantic validation.

    Args:
        annotated: The analysis result for a single function.

    Returns:
        A RoundingResult dict with all nested structures serialized.
    """
    sorted_lines = sorted(annotated.lines.values(), key=_line_sort_key)

    return RoundingResult(
        function_name=annotated.function_name,
        contract_name=annotated.contract_name,
        filename=annotated.filename,
        start_line=annotated.start_line,
        end_line=annotated.end_line,
        lines=[serialize_line(line) for line in sorted_lines],
        return_tags={
            name: serialize_tag_set(tags)
            for name, tags in annotated.return_tags.items()
        },
        inconsistencies=[
            serialize_finding(finding)
            for finding in annotated.inconsistencies
        ],
        annotation_mismatches=[
            serialize_finding(finding)
            for finding in annotated.annotation_mismatches
        ],
        traces={
            name: serialize_trace_node(trace)
            for name, trace in annotated.traces.items()
        },
    )


def _line_sort_key(line: AnnotatedLine) -> int:
    """Sort key for AnnotatedLine by line number."""
    return line.line_number
