"""Interprocedural rounding analysis with function summaries."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import RoundingTag
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.return_operation import Return


class TagSourceType(Enum):
    """Type of tag source."""

    DIRECT = auto()  # From direct operation (division, etc.)
    CALL = auto()  # From function call


@dataclass
class TagSource:
    """Source of a rounding tag - tracks how a tag was produced."""

    tag: RoundingTag
    source_type: TagSourceType
    callee_name: Optional[str] = None  # Function name if CALL
    description: Optional[str] = None  # e.g., "floor division"
    condition: Optional[str] = None  # Guarding condition if inside a branch

    def __str__(self) -> str:
        if self.source_type == TagSourceType.CALL and self.callee_name:
            return f"via {self.callee_name}()"
        elif self.description:
            return self.description
        return self.tag.name


@dataclass
class FunctionSummary:
    """Summary of possible rounding tags a function can return."""

    possible_tags: Set[RoundingTag] = field(default_factory=set)
    tag_sources: Dict[RoundingTag, List[TagSource]] = field(default_factory=dict)
    is_complete: bool = True
    incomplete_reason: Optional[str] = None

    def add_source(self, source: TagSource) -> None:
        """Add a tag source to the summary."""
        self.possible_tags.add(source.tag)
        if source.tag not in self.tag_sources:
            self.tag_sources[source.tag] = []
        self.tag_sources[source.tag].append(source)

    def get_sources_for_tag(self, tag: RoundingTag) -> List[TagSource]:
        """Get all sources that can produce a given tag."""
        return self.tag_sources.get(tag, [])

    def __str__(self) -> str:
        tags_str = ", ".join(sorted(t.name for t in self.possible_tags))
        completeness = "" if self.is_complete else f" (incomplete: {self.incomplete_reason})"
        return f"{{{tags_str}}}{completeness}"


class RoundingSummaryAnalyzer:
    """Analyzer that computes function summaries for interprocedural rounding analysis.

    Provides query-based API to check what rounding behaviors a function can produce.
    """

    def __init__(self, max_depth: int = 10) -> None:
        self._summaries: Dict[Function, FunctionSummary] = {}
        self._call_stack: Set[Function] = set()
        self._max_depth: int = max_depth

    def get_summary(self, function: Function) -> FunctionSummary:
        """Get or compute the summary for a function."""
        if function in self._summaries:
            return self._summaries[function]
        return self._compute_summary(function)

    def can_round(self, function: Function, tag: RoundingTag) -> bool:
        """Check if function can produce the given rounding tag."""
        summary = self.get_summary(function)
        return tag in summary.possible_tags

    def get_trace(
        self, function: Function, tag: RoundingTag, indent: int = 0
    ) -> List[str]:
        """Get a trace showing how a function can produce a given tag."""
        summary = self.get_summary(function)
        lines: List[str] = []
        prefix = "  " * indent

        if tag not in summary.possible_tags:
            return lines

        sources = summary.get_sources_for_tag(tag)
        if not sources:
            # Leaf node - direct return
            lines.append(f"{prefix}→ returns {tag.name}")
            return lines

        for source in sources:
            if source.source_type == TagSourceType.CALL and source.callee_name:
                # Show condition if present
                if source.condition:
                    lines.append(f"{prefix}└─ when {source.condition}")
                    lines.append(f"{prefix}   → {source.callee_name}()")
                    sub_indent = indent + 2
                else:
                    lines.append(f"{prefix}→ {source.callee_name}()")
                    sub_indent = indent + 1
                # Recursively get trace for callee
                callee = self._find_function_by_name(source.callee_name)
                if callee:
                    sub_trace = self.get_trace(callee, tag, sub_indent)
                    lines.extend(sub_trace)
            elif source.source_type == TagSourceType.DIRECT:
                desc = source.description or tag.name
                lines.append(f"{prefix}→ {desc}")

        return lines

    def _find_function_by_name(self, name: str) -> Optional[Function]:
        """Find a cached function by name."""
        for func in self._summaries:
            if func.name == name:
                return func
        return None

    def clear_cache(self) -> None:
        """Clear the summary cache."""
        self._summaries.clear()
        self._call_stack.clear()

    def _compute_summary(self, function: Function) -> FunctionSummary:
        """Compute the summary for a function."""
        # Check for recursion
        if function in self._call_stack:
            summary = FunctionSummary(
                possible_tags={RoundingTag.UNKNOWN},
                is_complete=False,
                incomplete_reason="recursive call detected",
            )
            return summary

        # Check depth limit
        if len(self._call_stack) >= self._max_depth:
            summary = FunctionSummary(
                possible_tags={RoundingTag.UNKNOWN},
                is_complete=False,
                incomplete_reason=f"depth limit ({self._max_depth}) exceeded",
            )
            return summary

        # Check if function has implementation
        if not function.nodes:
            summary = FunctionSummary(possible_tags={RoundingTag.NEUTRAL})
            self._summaries[function] = summary
            return summary

        # Add to call stack and compute
        self._call_stack.add(function)
        try:
            summary = self._analyze_function(function)
            self._summaries[function] = summary
            return summary
        finally:
            self._call_stack.discard(function)

    def _analyze_function(self, function: Function) -> FunctionSummary:
        """Run intraprocedural analysis and collect return tags with sources."""
        from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
            RoundingAnalysis,
        )

        analysis = RoundingAnalysis(summary_analyzer=self)
        engine = Engine.new(analysis, function)
        engine.run_analysis()
        node_results: Dict = engine.result()

        summary = FunctionSummary()
        var_sources: Dict[Variable, TagSource] = {}

        # Two-pass analysis: first collect sources, then trace returns
        self._collect_operation_sources(function, node_results, var_sources)
        self._collect_function_returns(function, node_results, var_sources, summary)

        if not summary.possible_tags:
            summary.possible_tags.add(RoundingTag.NEUTRAL)

        return summary

    def _collect_operation_sources(
        self,
        function: Function,
        node_results: Dict,
        var_sources: Dict[Variable, TagSource],
    ) -> None:
        """First pass: collect tag sources from call and division operations."""
        for node in function.nodes:
            if node not in node_results:
                continue

            state: AnalysisState = node_results[node]
            if state.post.variant != DomainVariant.STATE:
                continue

            domain: RoundingDomain = state.post
            if not node.irs_ssa:
                continue

            for operation in node.irs_ssa:
                self._track_operation_source(operation, domain, var_sources, node)

    def _track_operation_source(
        self,
        operation: object,
        domain: RoundingDomain,
        var_sources: Dict[Variable, TagSource],
        node: object,
    ) -> None:
        """Track source for a single operation (call or division)."""
        from slither.slithir.operations.binary import Binary, BinaryType
        from slither.slithir.operations.internal_call import InternalCall

        if isinstance(operation, InternalCall) and operation.lvalue:
            callee = operation.function
            if isinstance(callee, Function):
                lvalue = operation.lvalue
                if isinstance(lvalue, Variable):
                    tag = domain.state.get_tag(lvalue)
                    if tag != RoundingTag.NEUTRAL:
                        condition = self._get_guarding_condition(node)
                        var_sources[lvalue] = TagSource(
                            tag=tag,
                            source_type=TagSourceType.CALL,
                            callee_name=callee.name,
                            condition=condition,
                        )

        elif isinstance(operation, Binary) and operation.lvalue:
            if operation.type == BinaryType.DIVISION:
                lvalue = operation.lvalue
                if isinstance(lvalue, Variable):
                    tag = domain.state.get_tag(lvalue)
                    if tag != RoundingTag.NEUTRAL:
                        desc = "ceiling division" if tag == RoundingTag.UP else "floor division"
                        var_sources[lvalue] = TagSource(
                            tag=tag,
                            source_type=TagSourceType.DIRECT,
                            description=desc,
                        )

    def _get_guarding_condition(self, node: object) -> Optional[str]:
        """Extract the guarding condition from the node's dominating IF node."""
        from slither.core.cfg.node import Node, NodeType

        if not isinstance(node, Node):
            return None

        # Walk through dominators to find the nearest IF node
        for dominator in node.dominators:
            if dominator.type == NodeType.IF and dominator.expression:
                return str(dominator.expression)

        return None

    def _collect_function_returns(
        self,
        function: Function,
        node_results: Dict,
        var_sources: Dict[Variable, TagSource],
        summary: FunctionSummary,
    ) -> None:
        """Second pass: collect return tags and trace back to sources."""
        for node in function.nodes:
            if node not in node_results:
                continue

            state = node_results[node]
            if state.post.variant != DomainVariant.STATE:
                continue

            domain = state.post
            if not node.irs_ssa:
                continue

            for operation in node.irs_ssa:
                if isinstance(operation, Return):
                    self._collect_return_sources(operation, domain, var_sources, summary)

    def _collect_return_sources(
        self,
        operation: Return,
        domain: RoundingDomain,
        var_sources: Dict[Variable, TagSource],
        summary: FunctionSummary,
    ) -> None:
        """Collect return tags and their sources."""
        for return_value in operation.values:
            if isinstance(return_value, Variable):
                tag = domain.state.get_tag(return_value)

                # Check if we have a tracked source for this variable
                if return_value in var_sources:
                    summary.add_source(var_sources[return_value])
                else:
                    # Try to find source through producer chain
                    source = self._trace_variable_source(return_value, domain, var_sources)
                    if source:
                        summary.add_source(source)
                    else:
                        # No tracked source, add as direct
                        summary.add_source(TagSource(
                            tag=tag,
                            source_type=TagSourceType.DIRECT,
                            description=f"returns {tag.name}",
                        ))
            else:
                # Non-variable returns are NEUTRAL
                summary.add_source(TagSource(
                    tag=RoundingTag.NEUTRAL,
                    source_type=TagSourceType.DIRECT,
                    description="constant",
                ))

    def _trace_variable_source(
        self,
        var: Variable,
        domain: RoundingDomain,
        var_sources: Dict[Variable, TagSource],
    ) -> Optional[TagSource]:
        """Trace a variable back to its source through assignments."""
        visited: Set[Variable] = set()
        current = var

        while current and current not in visited:
            visited.add(current)

            if current in var_sources:
                return var_sources[current]

            # Get the producer operation
            producer = domain.state.get_producer(current)
            if not producer:
                break

            # Check for assignment chain
            from slither.slithir.operations.assignment import Assignment
            if isinstance(producer, Assignment) and isinstance(producer.rvalue, Variable):
                current = producer.rvalue
            else:
                break

        return None
