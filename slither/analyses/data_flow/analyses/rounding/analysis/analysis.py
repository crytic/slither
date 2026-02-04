"""Rounding analysis for Slither data-flow."""

from typing import TYPE_CHECKING, Optional, cast

from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
    RoundingDomain,
)
from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
)
from slither.analyses.data_flow.analyses.rounding.operations.registry import (
    OperationHandlerRegistry,
)
from slither.analyses.data_flow.engine.analysis import Analysis
from slither.analyses.data_flow.engine.direction import Direction, Forward
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.logger import get_logger
from slither.core.cfg.node import Node, NodeType
from slither.core.variables.variable import Variable
from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.rounding.analysis.interprocedural import (
        RoundingInterproceduralAnalyzer,
    )


class RoundingAnalysis(Analysis):
    """Analysis that tracks rounding direction metadata through data flow."""

    def __init__(
        self, interprocedural: Optional["RoundingInterproceduralAnalyzer"] = None
    ) -> None:
        self._direction: Direction = Forward()
        self._logger = get_logger(enable_ipython_embed=False, log_level="ERROR")
        self.inconsistencies: list[str] = []
        self.annotation_mismatches: list[str] = []
        self._interprocedural = interprocedural
        self._registry: OperationHandlerRegistry = OperationHandlerRegistry(self)

    def domain(self) -> Domain:
        """Return initial domain for analysis."""
        return RoundingDomain.bottom()

    def direction(self) -> Direction:
        """Return forward analysis direction."""
        return self._direction

    def bottom_value(self) -> Domain:
        """Return bottom element of domain lattice."""
        return RoundingDomain.bottom()

    def transfer_function(
        self,
        node: Node,
        domain: Domain,
        operation: Optional[Operation],
    ) -> None:
        """Core analysis logic - tag operations and propagate rounding metadata."""
        domain = cast(RoundingDomain, domain)

        if domain.variant == DomainVariant.BOTTOM:
            domain.variant = DomainVariant.STATE
            domain.state = RoundingState()

        self._initialize_entry_state(node, domain)
        self._dispatch_operation(operation, domain, node)

    def _dispatch_operation(
        self, operation: Optional[Operation], domain: RoundingDomain, node: Node
    ) -> None:
        """Dispatch operation to appropriate handler."""
        if operation is None:
            return

        handler = self._registry.get_handler(type(operation))
        if handler is not None:
            handler.handle(operation, domain, node)

    def _initialize_entry_state(self, node: Node, domain: RoundingDomain) -> None:
        """Initialize entry-point variables to NEUTRAL for consistent tag display."""
        if node.type not in (NodeType.ENTRYPOINT, NodeType.OTHER_ENTRYPOINT):
            return
        function = node.function
        if function is None:
            return
        contract = function.contract
        if contract is not None:
            for state_variable in contract.state_variables:
                domain.state.set_tag(state_variable, RoundingTag.NEUTRAL)
        for parameter in function.parameters:
            domain.state.set_tag(parameter, RoundingTag.NEUTRAL)
        for return_variable in function.returns:
            domain.state.set_tag(return_variable, RoundingTag.NEUTRAL)

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
            self.annotation_mismatches.append(message)
            self._logger.error(message)

    def _parse_expected_tag_from_name(self, name: str) -> Optional[RoundingTag]:
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
