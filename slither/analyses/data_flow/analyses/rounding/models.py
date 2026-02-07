"""Shared dataclasses for rounding analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from slither.analyses.data_flow.analyses.rounding.core.state import TagSet
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.core.cfg.node import Node


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
    inconsistencies: list[str] = field(default_factory=list)
    annotation_mismatches: list[str] = field(default_factory=list)
    node_results: dict[Node, AnalysisState] = field(default_factory=dict)


def get_node_line(node: Node) -> Optional[int]:
    """Get the primary source line for a node."""
    if node.source_mapping and node.source_mapping.lines:
        return node.source_mapping.lines[0]
    return None
