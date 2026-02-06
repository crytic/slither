"""DSPy module for structured rounding trace analysis."""

from typing import Optional

import dspy

from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingTag,
    TraceNode,
)
from slither.analyses.data_flow.analyses.rounding.explain.signature import (
    AnalyzeRoundingTrace,
    TraceAnalysis,
)
from slither.analyses.data_flow.logger import get_logger
from slither.core.declarations import Function

logger = get_logger()

MAX_SOURCE_LINES = 200


class TraceExplainer(dspy.Module):
    """Analyzes rounding trace chains via a typed LM prediction."""

    def __init__(self) -> None:
        super().__init__()
        self.analyze = dspy.Predict(AnalyzeRoundingTrace)

    def forward(
        self,
        trace_chain: str,
        traced_tag: str,
        solidity_source: str,
        contract_context: str,
    ) -> TraceAnalysis:
        """Return structured analysis for a rounding trace chain."""
        prediction = self.analyze(
            trace_chain=trace_chain,
            traced_tag=traced_tag,
            solidity_source=solidity_source,
            contract_context=contract_context,
        )
        return prediction.analysis


def serialize_trace_chain(
    trace: TraceNode,
    filter_tag: RoundingTag,
    indent: int = 0,
) -> str:
    """Serialize a trace tree into an indented string for the LM."""
    prefix = "  " * indent + ("└── " if indent > 0 else "")
    lines = [f"{prefix}{trace.source}"]
    for child in trace.children:
        if trace_contains_tag(child, filter_tag):
            child_text = serialize_trace_chain(child, filter_tag, indent + 1)
            lines.append(child_text)
    return "\n".join(lines)


def trace_contains_tag(trace: TraceNode, tag: RoundingTag) -> bool:
    """Check if a trace or any of its children contain the specified tag."""
    if tag in trace.tags:
        return True
    return any(trace_contains_tag(child, tag) for child in trace.children)


def split_trace_paths(
    trace: TraceNode,
    filter_tag: RoundingTag,
) -> list[list[TraceNode]]:
    """Split a trace tree into linear root-to-leaf paths for the filter tag.

    Each returned list is one path from the root to a leaf node that
    matches the filter tag, with no branching.
    """
    matching_children = [
        child for child in trace.children if trace_contains_tag(child, filter_tag)
    ]
    if not matching_children:
        return [[trace]]
    paths: list[list[TraceNode]] = []
    for child in matching_children:
        for sub_path in split_trace_paths(child, filter_tag):
            paths.append([trace, *sub_path])
    return paths


def serialize_trace_path(path: list[TraceNode]) -> str:
    """Serialize a linear trace path into an indented string for the LM."""
    lines: list[str] = []
    for index, node in enumerate(path):
        prefix = "  " * index + ("└── " if index > 0 else "")
        lines.append(f"{prefix}{node.source}")
    return "\n".join(lines)


def collect_path_functions(path: list[TraceNode]) -> list[str]:
    """Collect function names from a linear trace path."""
    return [node.function_name for node in path]


def collect_trace_functions(
    trace: TraceNode,
    filter_tag: RoundingTag,
) -> list[str]:
    """Walk the trace tree and collect function names matching the tag."""
    names: list[str] = []
    if filter_tag in trace.tags:
        names.append(trace.function_name)
    for child in trace.children:
        if trace_contains_tag(child, filter_tag):
            names.extend(collect_trace_functions(child, filter_tag))
    return names


def extract_source_for_path(
    path: list[TraceNode],
    function_lookup: dict[str, Function],
) -> str:
    """Extract Solidity source for each function in a linear path."""
    seen: set[str] = set()
    sections: list[str] = []
    for node in path:
        name = node.function_name
        if name in seen:
            continue
        seen.add(name)
        source_text = _get_function_source(name, function_lookup)
        sections.append(f"=== {name} ===\n{source_text}")
    return "\n\n".join(sections)


def extract_source_for_trace(
    trace: TraceNode,
    filter_tag: RoundingTag,
    function_lookup: dict[str, Function],
) -> str:
    """Extract Solidity source for each function in the trace chain."""
    function_names = collect_trace_functions(trace, filter_tag)
    seen: set[str] = set()
    sections: list[str] = []
    for name in function_names:
        if name in seen:
            continue
        seen.add(name)
        source_text = _get_function_source(name, function_lookup)
        sections.append(f"=== {name} ===\n{source_text}")
    return "\n\n".join(sections)


def build_function_lookup(
    functions: list[Function],
) -> dict[str, Function]:
    """Build a name-to-Function mapping from a list of functions."""
    lookup: dict[str, Function] = {}
    for function in functions:
        lookup[function.name] = function
    return lookup


def _get_function_source(
    name: str,
    function_lookup: dict[str, Function],
) -> str:
    """Get source text for a function, with truncation for long bodies."""
    function = function_lookup.get(name)
    if function is None:
        return "(source not available)"
    source_content: Optional[str] = None
    if function.source_mapping:
        source_content = function.source_mapping.content
    if not source_content:
        return "(source not available)"
    lines = source_content.splitlines()
    if len(lines) > MAX_SOURCE_LINES:
        truncated = lines[:MAX_SOURCE_LINES]
        truncated.append(f"... ({len(lines) - MAX_SOURCE_LINES} lines truncated)")
        return "\n".join(truncated)
    return source_content
