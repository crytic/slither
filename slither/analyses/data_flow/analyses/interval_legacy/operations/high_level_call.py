"""Handler for high-level external calls in interval analysis."""

from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.engine.interprocedural import InterproceduralAnalyzer
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.high_level_call import HighLevelCall

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class HighLevelCallHandler(BaseOperationHandler):
    """Handler for high-level external calls (calls to other contracts).

    When the called function is known (resolved), uses interprocedural analysis.
    Otherwise, treats the return value as unconstrained (full range).
    """

    def handle(
        self, operation: Optional[HighLevelCall], domain: IntervalDomain, node: "Node"
    ) -> None:
        if operation is None:
            return

        self.logger.debug(
            "Handling high-level call: {operation}",
            operation=operation,
        )

        if self.solver is None:
            self.logger.warning("Solver is None, skipping high-level call")
            return

        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping high-level call")
            return

        # Check if the called function is known and we can do interprocedural analysis
        called_function = operation.function
        if isinstance(called_function, Function) and self.analysis is not None:
            self._handle_interprocedural(operation, domain, called_function)
        else:
            self._handle_unconstrained(operation, domain)

    def _handle_interprocedural(
        self,
        operation: HighLevelCall,
        domain: IntervalDomain,
        called_function: Function,
    ) -> None:
        """Handle high-level call with interprocedural analysis when function is known."""
        self.logger.debug(
            "Using interprocedural analysis for high-level call to '{name}'",
            name=called_function.name,
        )

        # Delegate to the central interprocedural analyzer
        analyzer = InterproceduralAnalyzer(
            solver=self.solver,
            analysis=self.analysis,
            call_type_label="high-level",
        )
        analyzer.analyze_call(operation, domain)

    def _handle_unconstrained(
        self,
        operation: HighLevelCall,
        domain: IntervalDomain,
    ) -> None:
        """Fallback: treat return value as unconstrained when function is unknown."""
        # Get the lvalue (return value) of the call
        lvalue = operation.lvalue
        if lvalue is None:
            self.logger.debug("High-level call has no lvalue, nothing to track")
            return

        lvalue_name = IntervalSMTUtils.resolve_variable_name(lvalue)
        if lvalue_name is None:
            self.logger.debug("Could not resolve lvalue name for high-level call")
            return

        # Resolve the return type
        return_type: Optional[ElementaryType] = None
        if hasattr(lvalue, "type"):
            return_type = IntervalSMTUtils.resolve_elementary_type(lvalue.type)

        if return_type is None:
            self.logger.debug(
                "Could not resolve return type for high-level call lvalue: {lvalue}",
                lvalue=lvalue_name,
            )
            return

        if IntervalSMTUtils.solidity_type_to_smt_sort(return_type) is None:
            self.logger.debug(
                "Unsupported return type for high-level call: {type}",
                type=return_type,
            )
            return

        # Create a tracked variable for the return value with full range (unconstrained)
        lvalue_tracked = IntervalSMTUtils.get_tracked_variable(domain, lvalue_name)
        if lvalue_tracked is None:
            lvalue_tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, lvalue_name, return_type
            )
            if lvalue_tracked is None:
                return
            domain.state.set_range_variable(lvalue_name, lvalue_tracked)
            lvalue_tracked.assert_no_overflow(self.solver)

        self.logger.debug(
            "Created unconstrained return variable for high-level call: {lvalue}",
            lvalue=lvalue_name,
        )
