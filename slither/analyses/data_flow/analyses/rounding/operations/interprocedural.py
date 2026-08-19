"""Interprocedural call handler for rounding analysis.

One handler covers InternalCall, HighLevelCall, and LibraryCall. Tags
are inferred with a priority chain — inline annotation, name inference,
known-library lookup, callee body analysis, NEUTRAL default — where
body analysis runs a real nested engine fixpoint via
``RoundingAnalysis.analyze_call``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.rounding.core.models import RoundingFinding
from slither.analyses.data_flow.analyses.rounding.core.state import (
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
    lookup_inline_round_tag,
    lookup_known_tag,
)
from slither.analyses.data_flow.engine.interprocedural import (
    iter_matching_unpacks,
    resolve_callee,
)
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.variables.tuple import TupleVariable

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        RoundingDomain,
    )

logger = logging.getLogger("DataFlow")


class InterproceduralHandler(BaseOperationHandler):
    """Handler for call operations requiring interprocedural analysis.

    Callee resolution is delegated to ``resolve_callee`` and body
    analysis to ``RoundingAnalysis.analyze_call``, which runs a nested
    engine fixpoint guarded against recursion.
    """

    def handle(
        self,
        operation: Call,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Process call with name-based inference, falling back to body analysis."""
        if not operation.lvalue:
            logger.debug("Call has no lvalue, skipping: %s", operation)
            return

        function_name = _get_function_name(operation)

        if self._is_named_division_function(function_name):
            self._check_named_division_consistency(operation, domain, node)

        if isinstance(operation.lvalue, TupleVariable):
            self._handle_tuple_call(operation, function_name, domain, node)
            return

        tags, trace = self._infer_tag_with_fallback(operation, function_name, domain, node)
        self._set_tags(operation.lvalue, tags, operation, node, domain, trace)

    def _handle_tuple_call(
        self,
        operation: Call,
        function_name: str,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Handle a call whose lvalue is a TupleVariable.

        Resolves the callee, runs a nested fixpoint over its body, then
        sets tags directly on Unpack lvalues found in the same node.
        """
        called_function = resolve_callee(operation)
        if called_function is None:
            logger.debug("Tuple call %s: callee unresolvable, skipping", function_name)
            return

        summary = self.analysis.analyze_call(called_function, operation.arguments, domain, node)
        if summary is None:
            logger.debug("Tuple call %s: callee has no body, skipping", function_name)
            return
        if summary.from_recursion:
            logger.debug("Tuple call %s: recursion guard, skipping", function_name)
            return

        if not summary.per_index:
            message = f"Tuple call {function_name}: analyzed body but found no return tags"
            logger.error(message)
            raise RuntimeError(message)

        line_number = node.source_mapping.lines[0] if node.source_mapping else None
        self._apply_tuple_tags_to_unpacks(
            operation,
            summary.per_index,
            function_name,
            line_number=line_number,
            domain=domain,
            node=node,
        )

    def _apply_tuple_tags_to_unpacks(
        self,
        operation: Call,
        per_index: list[tuple[TagSet, list[TraceNode]]],
        function_name: str,
        *,
        line_number: int | None,
        domain: RoundingDomain,
        node: Node,
    ) -> None:
        """Set per-index tags directly on Unpack lvalues in this node."""
        all_tags: set[RoundingTag] = set()
        for unpack in iter_matching_unpacks(node, operation.lvalue):
            index = unpack.index
            if index >= len(per_index):
                logger.warning(
                    "Tuple call %s: unpack index %d exceeds return count %d, skipping",
                    function_name,
                    index,
                    len(per_index),
                )
                continue
            tags, traces = per_index[index]
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=tags,
                source=(f"{function_name}()[{index}] → {_format_tagset(tags)}"),
                children=traces,
            )
            domain.state.set_tag(
                unpack.lvalue,
                tags,
                unpack,
                trace=trace,
            )
            all_tags.update(tags)

        if all_tags:
            combined = frozenset(all_tags)
            domain.state.set_tag(
                operation.lvalue,
                combined,
                operation,
            )

    def _lookup_inline_annotation(
        self,
        node: Node,
        function_name: str,
    ) -> RoundingTag | None:
        """Check for an inline //@round annotation matching a function call.

        Scans all source lines of the node for //@round annotations
        and returns the tag for the given function name if found.

        Args:
            node: The CFG node containing the call.
            function_name: The function name to look up.

        Returns:
            RoundingTag if annotated, None otherwise.
        """
        if node.source_mapping is None:
            return None
        filename = node.source_mapping.filename.absolute
        crytic = node.compilation_unit.core.crytic_compile
        for line_number in node.source_mapping.lines:
            raw_bytes = crytic.get_code_from_line(filename, line_number)
            if raw_bytes is None:
                continue
            tag = lookup_inline_round_tag(raw_bytes.decode("utf8"), function_name)
            if tag is not None:
                return tag
        return None

    def _infer_tag_with_fallback(
        self,
        operation: Call,
        function_name: str,
        domain: RoundingDomain,
        node: Node,
    ) -> tuple[TagSet, TraceNode | None]:
        """Infer tags: inline annotation > name > known library > body analysis.

        Returns (tags, trace) where trace captures the call provenance if available.
        """
        line_number = node.source_mapping.lines[0] if node.source_mapping else None

        inline_tag = self._lookup_inline_annotation(node, function_name)
        if inline_tag is not None:
            logger.debug("%s: resolved via inline annotation → %s", function_name, inline_tag.name)
            inline_tags = frozenset({inline_tag})
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=inline_tags,
                source=f"{function_name}() → {inline_tag.name} (inline annotation)",
            )
            return inline_tags, trace

        tag = infer_tag_from_name(function_name)
        if tag != RoundingTag.NEUTRAL:
            logger.debug("%s: resolved via name inference → %s", function_name, tag.name)
            tags = frozenset({tag})
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=tags,
                source=f"{function_name}() → {tag.name}",
            )
            return tags, trace

        called_function = resolve_callee(operation)

        known = _lookup_known_function_tag(called_function, function_name, self.analysis.known_tags)
        if known is not None:
            logger.debug("%s: resolved via known library → %s", function_name, known.name)
            known_tags = frozenset({known})
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=known_tags,
                source=f"{function_name}() → {known.name} (known library)",
            )
            return known_tags, trace

        if called_function is None:
            logger.debug("%s: callee unresolvable, defaulting to NEUTRAL", function_name)
            return frozenset({RoundingTag.NEUTRAL}), None

        summary = self.analysis.analyze_call(called_function, operation.arguments, domain, node)
        body_tags = summary.tags if summary is not None else None
        if body_tags:
            logger.debug(
                "%s: resolved via body analysis → %s",
                function_name,
                _format_tagset(body_tags),
            )
            trace = TraceNode(
                function_name=function_name,
                line_number=line_number,
                tags=body_tags,
                source=f"{function_name}() returns {_format_tagset(body_tags)}",
                children=summary.traces if summary is not None else [],
            )
            return body_tags, trace
        logger.debug("%s: all inference steps exhausted, defaulting to NEUTRAL", function_name)
        return frozenset({tag}), None

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
    ) -> str | None:
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
        self.analysis.record_inconsistency(RoundingFinding(message=message, node=node))
        logger.warning(message)
        return reason

    def _set_tag(
        self,
        variable: Variable | None,
        tag: RoundingTag,
        operation: Call,
        node: Node,
        domain: RoundingDomain,
    ) -> None:
        """Set tag and check annotation."""
        if variable is None:
            return
        domain.state.set_tag(variable, tag, operation)
        self.analysis._check_annotation_for_variable(variable, tag, operation, node, domain)

    def _set_tags(
        self,
        variable: Variable | None,
        tags: TagSet,
        operation: Call,
        node: Node,
        domain: RoundingDomain,
        trace: TraceNode | None = None,
    ) -> None:
        """Set tag set, trace, and check annotation."""
        if variable is None:
            return
        domain.state.set_tag(variable, tags, operation, trace=trace)
        actual_tag = domain.state.get_tag(variable)
        self.analysis._check_annotation_for_variable(variable, actual_tag, operation, node, domain)


def _get_function_name(operation: Call) -> str:
    """Extract the called function's display name for name-based inference.

    ``LibraryCall`` subclasses ``HighLevelCall``, so one branch covers
    both; ``InternalCall`` exposes the Function directly.
    """
    if isinstance(operation, InternalCall):
        if operation.function:
            return operation.function.name
        return str(operation.function_name)
    if isinstance(operation, HighLevelCall):
        return str(operation.function_name.value)
    return ""


def _lookup_known_function_tag(
    called_function: Function | None,
    function_name: str,
    known_tags: dict[tuple[str, str], RoundingTag] | None,
) -> RoundingTag | None:
    """Check if function matches a known library rounding pattern.

    First tries exact (contract_name, function_name) match. Falls back to
    function-name-only match so interface calls (where the callee body is
    unavailable) can still resolve via the safe-libs DB.
    """
    if known_tags is None:
        return None
    if isinstance(called_function, FunctionContract):
        contract_name = called_function.contract_declarer.name
        tag = lookup_known_tag(contract_name, function_name, known_tags)
        if tag is not None:
            return tag
    return next(
        (tag for (_contract, fn), tag in known_tags.items() if fn == function_name),
        None,
    )


def _format_tagset(tags: TagSet) -> str:
    """Format a tag set for display in trace sources."""
    if len(tags) == 1:
        return next(iter(tags)).name
    names = sorted(tag.name for tag in tags)
    return "{" + ", ".join(names) + "}"
