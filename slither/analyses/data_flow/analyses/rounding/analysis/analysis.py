"""Rounding analysis for Slither data-flow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

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
from slither.analyses.data_flow.analyses.rounding.core.models import (
    RoundingCallSummary,
    RoundingFinding,
    get_node_line,
)
from slither.analyses.data_flow.analyses.rounding.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
    get_variable_tag,
)
from slither.analyses.data_flow.engine.analysis import Analysis, AnalysisState
from slither.analyses.data_flow.engine.cfg_utils import find_branch_condition
from slither.analyses.data_flow.engine.interprocedural import InterproceduralAnalysis

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
        KnownLibraryTags,
    )
    from slither.core.declarations.function import Function
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.variable import Variable
from slither.slithir.operations.operation import Operation
from slither.slithir.operations.return_operation import Return
from slither.slithir.variables.tuple import TupleVariable

logger = logging.getLogger("DataFlow")


class RoundingAnalysis(InterproceduralAnalysis[RoundingCallSummary]):
    """Analysis that tracks rounding direction metadata through data flow."""

    def __init__(
        self,
        known_tags: KnownLibraryTags | None = None,
    ) -> None:
        super().__init__()
        self._direction: Direction = Forward()
        self.inconsistencies: list[RoundingFinding] = []
        self.annotation_mismatches: list[RoundingFinding] = []
        self._seen_inconsistencies: set[tuple[str, int | None]] = set()
        self._seen_annotation_mismatches: set[tuple[str, int | None]] = set()
        self.known_tags: KnownLibraryTags | None = known_tags
        self._registry: OperationHandlerRegistry = OperationHandlerRegistry(self)

    def record_inconsistency(self, finding: RoundingFinding) -> None:
        """Append an inconsistency, deduplicating by (message, line).

        While body analysis is running, the finding's node is overridden to
        point at the user-visible call site rather than the callee's
        internal node.
        """
        finding = self._reattribute_to_caller(finding)
        line = get_node_line(finding.node) if finding.node is not None else None
        key = (finding.message, line)
        if key in self._seen_inconsistencies:
            return
        self._seen_inconsistencies.add(key)
        self.inconsistencies.append(finding)

    def record_annotation_mismatch(self, finding: RoundingFinding) -> None:
        """Append an annotation mismatch, deduplicating by (message, line)."""
        finding = self._reattribute_to_caller(finding)
        line = get_node_line(finding.node) if finding.node is not None else None
        key = (finding.message, line)
        if key in self._seen_annotation_mismatches:
            return
        self._seen_annotation_mismatches.add(key)
        self.annotation_mismatches.append(finding)

    def _reattribute_to_caller(self, finding: RoundingFinding) -> RoundingFinding:
        """If body analysis is active, retag the finding to the call site."""
        caller = self.outermost_call_site()
        if caller is None:
            return finding
        return RoundingFinding(
            message=finding.message,
            node=caller,
            variable=finding.variable,
        )

    def domain(self) -> Domain:
        """Return initial domain for analysis."""
        return RoundingDomain.bottom()

    def direction(self) -> Direction:
        """Return forward analysis direction."""
        return self._direction

    def bottom_value(self) -> Domain:
        """Return bottom element of domain lattice."""
        return RoundingDomain.bottom()

    def prepare_for_function(self, function: Function) -> None:
        """No per-function preparation is needed for rounding analysis.

        This must stay a no-op (or become re-entrant): nested engines
        created by ``analyze_call`` invoke it on this same instance
        mid-run of the caller's engine, so any per-function state cached
        here would be clobbered and not restored.
        """

    def bind_arguments(
        self,
        callee: Function,
        arguments: list[Variable],
        caller_domain: Domain,
    ) -> Domain:
        """Build the callee entry domain from caller argument tags.

        Collapses each argument's tag set to a single tag via
        ``get_variable_tag`` (multi-tag arguments become UNKNOWN) and
        also binds same-named SSA reads in the callee body, since
        Slither's SSA uses distinct variable instances for parameters
        vs body reads and ``RoundingState`` lookups are instance-keyed.
        """
        caller = cast("RoundingDomain", caller_domain)
        entry = RoundingDomain(DomainVariant.STATE, RoundingState())
        param_name_to_tag: dict[str, RoundingTag] = {}
        for parameter, argument in zip(callee.parameters, arguments, strict=False):
            argument_tag = get_variable_tag(argument, caller)
            entry.state.set_tag(parameter, argument_tag)
            param_name_to_tag[parameter.name] = argument_tag
        self._bind_ssa_reads(callee, param_name_to_tag, entry)
        return entry

    def _bind_ssa_reads(
        self,
        callee: Function,
        param_name_to_tag: dict[str, RoundingTag],
        entry: RoundingDomain,
    ) -> None:
        """Seed tags onto SSA variable reads whose base name matches a parameter."""
        bound_vars: set[Variable] = set()
        for node in callee.nodes:
            if not node.irs_ssa:
                continue
            for operation in node.irs_ssa:
                for variable in operation.read:
                    if not isinstance(variable, Variable):
                        continue
                    if variable in bound_vars:
                        continue
                    if variable.name in param_name_to_tag:
                        entry.state.set_tag(variable, param_name_to_tag[variable.name])
                        bound_vars.add(variable)

    def extract_return_summary(
        self,
        callee: Function,
        results: dict[Node, AnalysisState[Analysis]],
    ) -> RoundingCallSummary | None:
        """Summarize return tags and traces from the callee's fixpoint results.

        Reads each Return node's post state. Scalar tags union the
        first return value's tags across all Return nodes (absorbing
        NEUTRAL when mixed); per-index tags come from the first Return
        node only.

        The extraction order below — tags, then per_index, then traces
        — is load-bearing. The per-index pass and the scalar-trace pass
        both stamp ``branch_condition`` on the SAME TraceNode objects
        (``get_trace`` returns shared references, not copies), so the
        last write wins: the scalar-trace pass runs last and its stamp
        is what trace display shows. Reordering these calls changes
        trace output.

        One accepted behavioral residual vs the pre-refactor code: for
        a multi-return tuple callee whose Return statements share a
        return-value TraceNode, ``branch_condition`` is now stamped by
        the scalar-trace pass over every Return node instead of the old
        first-Return-only tuple path. This is display metadata only;
        tags and findings are unaffected.
        """
        tags = self._extract_return_tags(callee, results)
        per_index = self._extract_per_index_return_tags(callee, results)
        traces = self._extract_return_traces(callee, results)
        return RoundingCallSummary(tags=tags, traces=traces, per_index=per_index)

    def on_recursion(self, callee: Function) -> RoundingCallSummary:
        """Conservative summary for recursive (or depth-capped) calls.

        Scalar call sites see ``{UNKNOWN}``, matching the historical
        recursion-guard behavior; tuple call sites check
        ``from_recursion`` and skip silently instead of raising on the
        empty ``per_index``.
        """
        return RoundingCallSummary(
            tags=frozenset({RoundingTag.UNKNOWN}),
            traces=[],
            per_index=[],
            from_recursion=True,
        )

    def _extract_return_tags(
        self,
        callee: Function,
        results: dict[Node, AnalysisState[Analysis]],
    ) -> TagSet | None:
        """Union first-return-value tags across all Return nodes."""
        all_tags: set[RoundingTag] = set()
        for node in callee.nodes:
            post = cast("RoundingDomain", results[node].post)
            all_tags.update(self._return_tags_from_node(node, post))
        if not all_tags:
            return None
        if len(all_tags) > 1 and RoundingTag.NEUTRAL in all_tags:
            all_tags.discard(RoundingTag.NEUTRAL)
        return frozenset(all_tags)

    def _return_tags_from_node(
        self,
        node: Node,
        post: RoundingDomain,
    ) -> set[RoundingTag]:
        """Get first-return-value tags from a node's Return operations."""
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
                tags.update(post.state.get_tags(return_value))
        return tags

    def _extract_return_traces(
        self,
        callee: Function,
        results: dict[Node, AnalysisState[Analysis]],
    ) -> list[TraceNode]:
        """Collect first-return-value traces from every Return node."""
        traces: list[TraceNode] = []
        for node in callee.nodes:
            post = cast("RoundingDomain", results[node].post)
            traces.extend(self._return_traces_from_node(node, post))
        return traces

    def _return_traces_from_node(
        self,
        node: Node,
        post: RoundingDomain,
    ) -> list[TraceNode]:
        """Get traces from a node's Return operations, stamping the branch guard."""
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
                trace = post.state.get_trace(return_value)
                if trace is not None:
                    trace.branch_condition = find_branch_condition(node)
                    traces.append(trace)
        return traces

    def _extract_per_index_return_tags(
        self,
        callee: Function,
        results: dict[Node, AnalysisState[Analysis]],
    ) -> list[tuple[TagSet, list[TraceNode]]]:
        """Per-index tags/traces from the FIRST Return node with values.

        Deliberately stops at the first Return node and pads
        TupleVariable returns by ``max(len(return_types), 1)`` —
        preserved quirks of the original extraction; multi-return tuple
        functions are not merged.
        """
        for node in callee.nodes:
            if not node.irs_ssa:
                continue
            for operation in node.irs_ssa:
                if not isinstance(operation, Return):
                    continue
                if not operation.values:
                    continue
                post = cast("RoundingDomain", results[node].post)
                return self._per_index_from_return(callee, node, operation, post)
        return []

    def _per_index_from_return(
        self,
        callee: Function,
        node: Node,
        operation: Return,
        post: RoundingDomain,
    ) -> list[tuple[TagSet, list[TraceNode]]]:
        """Extract (tags, traces) per return index from one Return operation."""
        condition = find_branch_condition(node)
        per_index: list[tuple[TagSet, list[TraceNode]]] = []
        for return_value in operation.values:
            if isinstance(return_value, TupleVariable):
                tuple_tags = post.state.get_tags(return_value)
                if not tuple_tags:
                    tuple_tags = frozenset({RoundingTag.NEUTRAL})
                tuple_trace = post.state.get_trace(return_value)
                trace_list = [tuple_trace] if tuple_trace else []
                return_types = callee.return_type or []
                count = max(len(return_types), 1)
                for _ in range(count):
                    per_index.append((tuple_tags, list(trace_list)))
            elif isinstance(return_value, Variable):
                tags = post.state.get_tags(return_value)
                trace = post.state.get_trace(return_value)
                if trace is not None:
                    trace.branch_condition = condition
                trace_list = [trace] if trace else []
                per_index.append((tags, trace_list))
            else:
                neutral = frozenset({RoundingTag.NEUTRAL})
                per_index.append((neutral, []))
        return per_index

    def transfer_function(
        self,
        node: Node,
        domain: Domain,
        operation: Operation | None,
    ) -> None:
        """Core analysis logic - tag operations and propagate rounding metadata."""
        domain = cast("RoundingDomain", domain)

        if domain.variant == DomainVariant.BOTTOM:
            domain.variant = DomainVariant.STATE
            domain.state = RoundingState()

        self._initialize_entry_state(node, domain)
        self._dispatch_operation(operation, domain, node)

    def _dispatch_operation(
        self, operation: Operation | None, domain: RoundingDomain, node: Node
    ) -> None:
        """Dispatch operation to appropriate handler."""
        if operation is None:
            return

        handler = self._registry.get_handler(type(operation))
        if handler is not None:
            handler.handle(operation, domain, node)

    def _initialize_entry_state(self, node: Node, domain: RoundingDomain) -> None:
        """Initialize entry-point variables to NEUTRAL for consistent tag display.

        Defaults are applied set-if-absent so that entry state seeded via
        ``Engine.new(entry_domain=...)`` is not clobbered.
        """
        if node.type not in (NodeType.ENTRYPOINT, NodeType.OTHER_ENTRYPOINT):
            return
        function = node.function
        if function is None:
            logger.debug("Entry node %s has no function, skipping init", node.node_id)
            return
        contract = function.contract
        if contract is None:
            logger.debug("Function %s has no contract, skipping state var init", function.name)
        entry_variables: list[Variable] = []
        if contract is not None:
            entry_variables.extend(contract.state_variables)
        entry_variables.extend(function.parameters)
        entry_variables.extend(function.returns)
        for variable in entry_variables:
            if not domain.state.has_tag(variable):
                domain.state.set_tag(variable, RoundingTag.NEUTRAL)

    def _check_annotation_for_variable(
        self,
        variable: Variable,
        actual_tag: RoundingTag,
        operation: Operation,
        node: Node,
        domain: RoundingDomain,
    ) -> None:
        """Validate variable annotation suffixes against inferred rounding."""
        expected_tag = self._parse_expected_tag_from_name(variable.name)
        # Skip variables without annotation suffixes to avoid noisy reporting.
        if expected_tag is None:
            return
        # Report when the inferred tag does not match the developer annotation.
        if actual_tag != expected_tag:
            node_function_name = node.function.name
            unknown_reason = domain.state.get_unknown_reason(variable)
            reason_suffix = f" ({unknown_reason})" if unknown_reason else ""
            message = (
                "Rounding annotation mismatch in "
                f"{node_function_name}: {variable.name} expected "
                f"{expected_tag.name} but inferred {actual_tag.name}"
                f"{reason_suffix} in {operation}"
            )
            self.record_annotation_mismatch(
                RoundingFinding(
                    message=message,
                    node=node,
                    variable=variable,
                )
            )
            logger.warning(message)

    def _parse_expected_tag_from_name(self, name: str) -> RoundingTag | None:
        """Parse annotation suffixes like _UP/_DOWN/_NEUTRAL from variable names."""
        name_upper = name.upper()
        suffix_to_tag = (
            ("_UP", RoundingTag.UP),
            ("_DOWN", RoundingTag.DOWN),
            ("_NEUTRAL", RoundingTag.NEUTRAL),
        )
        for suffix, tag in suffix_to_tag:
            if name_upper.endswith(suffix):
                return tag
        return None
