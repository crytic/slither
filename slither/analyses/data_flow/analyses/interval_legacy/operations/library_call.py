"""Handler for library calls in interval analysis."""

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.engine.interprocedural import InterproceduralAnalyzer
from slither.core.declarations.function import Function
from slither.slithir.operations.library_call import LibraryCall

if TYPE_CHECKING:
    from slither.core.cfg.node import Node


class LibraryCallHandler(BaseOperationHandler):
    """Handler for library function calls with interprocedural analysis.

    Delegates interprocedural analysis logic to the central InterproceduralAnalyzer.
    """

    def handle(self, operation: LibraryCall, domain: IntervalDomain, node: "Node") -> None:
        self.logger.debug("Handling library call: {operation}", operation=operation)

        if self.solver is None:
            self.logger.warning("Solver is None, skipping library call")
            return

        if self.analysis is None:
            self.logger.warning("Analysis instance is None, skipping interprocedural library call")
            return

        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping library call")
            return

        function = operation.function
        if not isinstance(function, Function):
            self.logger.debug("Library call function is not a Function instance, skipping")
            return

        # Delegate to the central interprocedural analyzer
        analyzer = InterproceduralAnalyzer(
            solver=self.solver,
            analysis=self.analysis,
            call_type_label="library",
        )
        analyzer.analyze_call(operation, domain)
