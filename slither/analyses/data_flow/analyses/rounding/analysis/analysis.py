"""Rounding analysis for Slither data-flow."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
)
from slither.analyses.data_flow.analyses.rounding.core.models import (
    RoundingFinding,
    get_node_line,
)
from slither.analyses.data_flow.analyses.rounding.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.engine.analysis import Analysis

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.operations.tag_operations import (
        KnownLibraryTags,
    )
    from slither.core.declarations.function import Function
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.logger import get_logger
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.variable import Variable
from slither.slithir.operations.operation import Operation


class RoundingAnalysis(Analysis):
    """Analysis that tracks rounding direction metadata through data flow."""

    def __init__(
        self,
        known_tags: KnownLibraryTags | None = None,
    ) -> None:
        self._direction: Direction = Forward()
        self._logger = get_logger(enable_ipython_embed=False, log_level="INFO")
        self.inconsistencies: list[RoundingFinding] = []
        self.annotation_mismatches: list[RoundingFinding] = []
        self._seen_inconsistencies: set[tuple[str, int | None]] = set()
        self._seen_annotation_mismatches: set[tuple[str, int | None]] = set()
        self._caller_node_stack: list[Node] = []
        self.known_tags: KnownLibraryTags | None = known_tags
        self._registry: OperationHandlerRegistry = OperationHandlerRegistry(self)

    def push_caller_node(self, node: Node) -> None:
        """Mark a node as the user-visible call site for findings recorded
        while body analysis runs underneath this call."""
        self._caller_node_stack.append(node)

    def pop_caller_node(self) -> None:
        """Match a prior push_caller_node call."""
        if self._caller_node_stack:
            self._caller_node_stack.pop()

    def _outermost_caller_node(self) -> Node | None:
        """Return the bottom-of-stack (topmost user-visible) caller node."""
        return self._caller_node_stack[0] if self._caller_node_stack else None

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
        caller = self._outermost_caller_node()
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
        """No per-function preparation is needed for rounding analysis."""

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
            self._logger.debug(
                "Entry node {nid} has no function, skipping init",
                nid=node.node_id,
            )
            return
        contract = function.contract
        if contract is None:
            self._logger.debug(
                "Function {name} has no contract, skipping state var init",
                name=function.name,
            )
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
                    message=message, node=node, variable=variable,
                )
            )
            self._logger.warning(message)

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
