"""Base handler for interprocedural analysis of function calls."""

from __future__ import annotations

from abc import abstractmethod
from typing import Optional

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
    TagSet,
    TraceNode,
)
from slither.analyses.data_flow.analyses.rounding.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    get_variable_tag,
    infer_tag_from_name,
)
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.return_operation import Return



class InterproceduralHandler(BaseOperationHandler):
    """Base handler for function calls requiring interprocedural analysis.

    Subclasses should implement:
    - _get_called_function: Extract the Function object from the operation
    - _get_function_name: Get the function name for name-based inference
    """

    def __init__(self, analysis) -> None:
        super().__init__(analysis)
        self._call_stack: set[Function] = set()

    def handle(
        self,
        operation: Call,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Process call with name-based inference, falling back to body analysis."""
        if not operation.lvalue:
            return

        function_name = self._get_function_name(operation)

        if self._is_named_division_function(function_name):
            self._check_named_division_consistency(operation, domain, node)

        tags, trace = self._infer_tag_with_fallback(operation, function_name, domain, node)
        self._set_tags(operation.lvalue, tags, operation, node, domain, trace)

    def _infer_tag_with_fallback(
        self,
        operation: Call,
        function_name: str,
        domain: RoundingDomain,
        node: Node,
    ) -> tuple[TagSet, Optional[TraceNode]]:
        """Infer tags from name first, then fall back to body analysis.

        Returns (tags, trace) where trace captures the call provenance if available.
        """
        tag = infer_tag_from_name(function_name)
        line_number = node.source_mapping.lines[0] if node.source_mapping else None

        if tag != RoundingTag.NEUTRAL:
            tags = frozenset({tag})
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=tags,
                source=f"{function_name}() → {tag.name}",
            )
            return tags, trace

        called_function = self._get_called_function(operation)
        if called_function is None:
            return frozenset({tag}), None

        body_tags, child_traces = self._analyze_function_body(
            called_function, operation.arguments, domain
        )
        if body_tags:
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=body_tags,
                source=f"{function_name}() returns {_format_tagset(body_tags)}",
                children=child_traces,
            )
            return body_tags, trace
        return frozenset({tag}), None

    @abstractmethod
    def _get_called_function(self, operation: Call) -> Function | None:
        """Extract the called Function, or None if not resolvable."""

    @abstractmethod
    def _get_function_name(self, operation: Call) -> str:
        """Get the function name for name-based inference."""

    def _analyze_function_body(
        self,
        function: Function,
        arguments: list,
        domain: RoundingDomain,
    ) -> tuple[TagSet | None, list[TraceNode]]:
        """Analyze function body with argument tag mapping.

        Returns (tags, child_traces) where tags is the set of all return value tags,
        and child_traces contains provenance from nested calls.
        """
        if function in self._call_stack:
            return frozenset({RoundingTag.UNKNOWN}), []

        if not function.nodes:
            return None, []

        self._call_stack.add(function)
        try:
            return self._run_interprocedural_analysis(function, arguments, domain)
        finally:
            self._call_stack.discard(function)

    def _run_interprocedural_analysis(
        self,
        function: Function,
        arguments: list,
        domain: RoundingDomain,
    ) -> tuple[TagSet | None, list[TraceNode]]:
        """Run analysis on callee function and extract return tags and traces."""
        callee_domain = RoundingDomain(DomainVariant.STATE, RoundingState())
        self._bind_parameter_tags(function, arguments, domain, callee_domain)
        self._analyze_callee_body(function, callee_domain)
        tags = self._extract_return_tags(function, callee_domain)
        traces = self._extract_return_traces(function, callee_domain)
        return tags, traces

    def _bind_parameter_tags(
        self,
        function: Function,
        arguments: list,
        caller_domain: RoundingDomain,
        callee_domain: RoundingDomain,
    ) -> None:
        """Map argument tags from caller to parameter variables in callee."""
        for parameter, argument in zip(function.parameters, arguments):
            argument_tag = get_variable_tag(argument, caller_domain)
            callee_domain.state.set_tag(parameter, argument_tag)

    def _analyze_callee_body(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> None:
        """Analyze the function body operations."""
        for node in function.nodes:
            self._analyze_node_operations(node, callee_domain)

    def _analyze_node_operations(
        self,
        node: Node,
        callee_domain: RoundingDomain,
    ) -> None:
        """Analyze all operations in a single node."""
        if not node.irs_ssa:
            return
        for operation in node.irs_ssa:
            handler = self.analysis._registry.get_handler(type(operation))
            if handler is not None:
                handler.handle(operation, callee_domain, node)

    def _extract_return_tags(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> TagSet | None:
        """Extract all return value tags from the analyzed function."""
        all_tags: set[RoundingTag] = set()
        for node in function.nodes:
            tags = self._get_return_tags_from_node(node, callee_domain)
            all_tags.update(tags)
        if not all_tags:
            return None
        if len(all_tags) > 1 and RoundingTag.NEUTRAL in all_tags:
            all_tags.discard(RoundingTag.NEUTRAL)
        return frozenset(all_tags)

    def _get_return_tags_from_node(
        self,
        node: Node,
        callee_domain: RoundingDomain,
    ) -> set[RoundingTag]:
        """Get return tags from a single node if it contains a return operation."""
        tags: set[RoundingTag] = set()
        if not node.irs_ssa:
            return tags
        for operation in node.irs_ssa:
            if not isinstance(operation, Return):
                continue
            if not operation.values:
                continue
            return_value = operation.values[0]
            if isinstance(return_value, Variable):
                tags.update(callee_domain.state.get_tags(return_value))
        return tags

    def _extract_return_traces(
        self,
        function: Function,
        callee_domain: RoundingDomain,
    ) -> list[TraceNode]:
        """Extract traces from return values in the analyzed function."""
        traces: list[TraceNode] = []
        for node in function.nodes:
            traces.extend(self._get_return_traces_from_node(node, callee_domain))
        return traces

    def _get_return_traces_from_node(
        self,
        node: Node,
        callee_domain: RoundingDomain,
    ) -> list[TraceNode]:
        """Get traces from return values in a single node."""
        traces: list[TraceNode] = []
        if not node.irs_ssa:
            return traces
        for operation in node.irs_ssa:
            if not isinstance(operation, Return):
                continue
            if not operation.values:
                continue
            return_value = operation.values[0]
            if isinstance(return_value, Variable):
                trace = callee_domain.state.get_trace(return_value)
                if trace is not None:
                    traces.append(trace)
        return traces

    def _is_named_division_function(self, function_name: str) -> bool:
        """Return True when function name indicates divUp/divDown helpers."""
        name_lower = function_name.lower()
        return "divup" in name_lower or "divdown" in name_lower

    def _check_named_division_consistency(
        self,
        operation: Call,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Enforce division consistency for divUp/divDown call arguments."""
        if len(operation.arguments) < 2:
            return

        numerator = operation.arguments[0]
        denominator = operation.arguments[1]
        numerator_tag = get_variable_tag(numerator, domain)
        denominator_tag = get_variable_tag(denominator, domain)
        inconsistency_reason = self._check_division_consistency(
            numerator_tag, denominator_tag, operation, node
        )
        if inconsistency_reason and operation.lvalue:
            domain.state.set_tag(
                operation.lvalue,
                RoundingTag.UNKNOWN,
                operation,
                unknown_reason=inconsistency_reason,
            )

    def _check_division_consistency(
        self,
        numerator_tag: RoundingTag,
        denominator_tag: RoundingTag,
        operation: Call,
        node: Node,
    ) -> Optional[str]:
        """Check numerator/denominator consistency for division operations."""
        if denominator_tag == RoundingTag.NEUTRAL:
            return None

        if numerator_tag != denominator_tag:
            return None

        function_name = node.function.name
        reason = (
            "Inconsistent division: numerator and denominator both "
            f"{numerator_tag.name} in {function_name}"
        )
        message = (
            "Division rounding inconsistency in "
            f"{function_name}: numerator and denominator both "
            f"{numerator_tag.name} in {operation}"
        )
        self.analysis.inconsistencies.append(message)
        self.analysis._logger.error(message)
        return reason

    def _set_tag(
        self,
        variable: Optional[Variable],
        tag: RoundingTag,
        operation: Call,
        node: Node,
        domain: RoundingDomain,
    ) -> None:
        """Set tag and check annotation."""
        if variable is None:
            return
        domain.state.set_tag(variable, tag, operation)
        self.analysis._check_annotation_for_variable(
            variable, tag, operation, node, domain
        )

    def _set_tags(
        self,
        variable: Optional[Variable],
        tags: TagSet,
        operation: Call,
        node: Node,
        domain: RoundingDomain,
        trace: Optional[TraceNode] = None,
    ) -> None:
        """Set tag set, trace, and check annotation."""
        if variable is None:
            return
        domain.state.set_tag(variable, tags, operation, trace=trace)
        actual_tag = domain.state.get_tag(variable)
        self.analysis._check_annotation_for_variable(
            variable, actual_tag, operation, node, domain
        )


def _format_tagset(tags: TagSet) -> str:
    """Format a tag set for display in trace sources."""
    if len(tags) == 1:
        return next(iter(tags)).name
    names = sorted(tag.name for tag in tags)
    return "{" + ", ".join(names) + "}"
