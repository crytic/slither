"""Shared serialization helpers for converting Slither IR to plain data.

These helpers form the boundary between Slither's internal IR types
(Node, Variable) and JSON-serializable plain types. Individual analyses
(rounding, taint) use these to build their specific serialization
without duplicating common IR-to-data conversions.

Analysis-specific serialization (e.g. RoundingTag, TraceNode) belongs
in each analysis's own serialize module, not here.
"""

from __future__ import annotations

from typing import TypedDict

from slither.core.cfg.node import Node
from slither.core.variables.variable import Variable


class AnalysisResult(TypedDict):
    """Common envelope for all data-flow analysis results.

    Every analysis result — both full (CLI --json) and summary (MCP) —
    carries these fields for identification and source navigation.
    """

    analysis: str
    function_name: str
    contract_name: str
    filename: str
    start_line: int
    end_line: int


class SourceLocation(TypedDict):
    """JSON-serializable source location extracted from a Slither Node."""

    filename: str
    line_number: int | None
    starting_column: int
    ending_column: int


def serialize_source_location(node: Node) -> SourceLocation:
    """Extract a JSON-serializable source location from a Node.

    Args:
        node: A Slither CFG node with source mapping.

    Returns:
        A SourceLocation dict with filename, line, and column info.
        Fields default to empty/zero when source mapping is absent.
    """
    mapping = node.source_mapping
    if mapping is None:
        return SourceLocation(
            filename="",
            line_number=None,
            starting_column=0,
            ending_column=0,
        )

    line_number: int | None = None
    if mapping.lines:
        line_number = mapping.lines[0]

    filename = ""
    if mapping.filename and mapping.filename.short:
        filename = mapping.filename.short

    return SourceLocation(
        filename=filename,
        line_number=line_number,
        starting_column=mapping.starting_column,
        ending_column=mapping.ending_column,
    )


def serialize_variable_ref(variable: Variable | None) -> str | None:
    """Extract the name from a Variable, or None if absent.

    Args:
        variable: A Slither Variable, or None.

    Returns:
        The variable's name string, or None.
    """
    if variable is None:
        return None
    return variable.name
