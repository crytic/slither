"""Rounding-specific serialization: full (CLI) and summary (MCP)."""

from __future__ import annotations

from typing import List, Optional, TypedDict

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
)
from slither.analyses.data_flow.analyses.rounding.core.models import (
    AnnotatedFunction,
    AnnotatedLine,
    LineAnnotation,
    RoundingFinding,
    get_node_line,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    TraceNode,
)
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.registry.serialization import (
    serialize_variable_ref,
)
from slither.core.variables.variable import Variable


# ── TypedDicts: full (CLI --json) ────────────────────────────────


class FindingDict(TypedDict):
    message: str
    line_number: Optional[int]
    variable_name: Optional[str]


class TraceNodeDict(TypedDict):
    function_name: str
    line_number: Optional[int]
    tags: List[str]
    source: str
    children: List[TraceNodeDict]
    branch_condition: Optional[str]


class AnnotationDict(TypedDict):
    variable_name: str
    tags: List[str]
    is_return: bool
    note: str


class AnnotatedLineDict(TypedDict):
    line_number: int
    source_text: str
    annotations: List[AnnotationDict]
    is_entry: bool


class RoundingResult(TypedDict):
    """Full serialized function for CLI ``--json`` output."""

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


# ── TypedDicts: summary (MCP ProjectFacts) ───────────────────────


class RoundingSummary(TypedDict):
    """Lightweight function summary for MCP caching."""

    function_name: str
    contract_name: str
    filename: str
    start_line: int
    end_line: int
    variable_tags: dict[str, List[str]]
    return_tags: dict[str, List[str]]
    inconsistencies: List[str]
    annotation_mismatches: List[str]


# ── Shared helpers ───────────────────────────────────────────────


def serialize_tag_set(tags: frozenset) -> List[str]:
    """Convert a TagSet to sorted name strings."""
    return sorted(tag.name for tag in tags)


# ── Full serialization (CLI) ────────────────────────────────────


def serialize_trace_node(
    trace: TraceNode,
    max_depth: int = 10,
) -> TraceNodeDict:
    """Recursively serialize a TraceNode provenance chain."""
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
    """Serialize a RoundingFinding with line/variable references."""
    return FindingDict(
        message=finding.message,
        line_number=get_node_line(finding.node),
        variable_name=serialize_variable_ref(finding.variable),
    )


def serialize_annotation(annotation: LineAnnotation) -> AnnotationDict:
    return AnnotationDict(
        variable_name=annotation.variable_name,
        tags=serialize_tag_set(annotation.tags),
        is_return=annotation.is_return,
        note=annotation.note,
    )


def serialize_line(line: AnnotatedLine) -> AnnotatedLineDict:
    return AnnotatedLineDict(
        line_number=line.line_number,
        source_text=line.source_text,
        annotations=[
            serialize_annotation(ann) for ann in line.annotations
        ],
        is_entry=line.is_entry,
    )


def serialize_annotated_function(
    annotated: AnnotatedFunction,
) -> RoundingResult:
    """Full serialization for CLI ``--json`` output."""
    sorted_lines = sorted(
        annotated.lines.values(), key=lambda line: line.line_number
    )
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
            serialize_finding(f) for f in annotated.inconsistencies
        ],
        annotation_mismatches=[
            serialize_finding(f) for f in annotated.annotation_mismatches
        ],
        traces={
            name: serialize_trace_node(trace)
            for name, trace in annotated.traces.items()
        },
    )


# ── Summary serialization (MCP) ─────────────────────────────────


def summarize_annotated_function(
    annotated: AnnotatedFunction,
) -> RoundingSummary:
    """Lightweight summary: variable tags + findings, no source/traces."""
    variable_tags = _extract_exit_variable_tags(annotated)
    return RoundingSummary(
        function_name=annotated.function_name,
        contract_name=annotated.contract_name,
        filename=annotated.filename,
        start_line=annotated.start_line,
        end_line=annotated.end_line,
        variable_tags=variable_tags,
        return_tags={
            name: serialize_tag_set(tags)
            for name, tags in annotated.return_tags.items()
        },
        inconsistencies=[
            f.message for f in annotated.inconsistencies
        ],
        annotation_mismatches=[
            f.message for f in annotated.annotation_mismatches
        ],
    )


def _extract_exit_variable_tags(
    annotated: AnnotatedFunction,
) -> dict[str, List[str]]:
    """Extract variable→tags from exit nodes, skipping NEUTRAL-only."""
    variable_tags: dict[str, List[str]] = {}
    for node, state in annotated.node_results.items():
        if node.sons:
            continue
        if state.post.variant != DomainVariant.STATE:
            continue
        post_state = state.post.state
        for variable, tags in post_state._tags.items():
            if not isinstance(variable, Variable):
                continue
            if not variable.name:
                continue
            tag_names = serialize_tag_set(tags)
            if tag_names == ["NEUTRAL"]:
                continue
            variable_tags[variable.name] = tag_names
    return variable_tags
