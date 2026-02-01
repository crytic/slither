"""Handler for internal function calls in interval analysis."""

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.engine.interprocedural import InterproceduralAnalyzer
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.slithir.operations.internal_call import InternalCall


class InternalCallHandler(BaseOperationHandler):
    """Handler for internal function calls with interprocedural analysis.

    Delegates interprocedural analysis logic to the central InterproceduralAnalyzer.
    """

    def handle(self, operation: InternalCall, domain: IntervalDomain, node: Node) -> None:
        self.logger.debug("Handling internal call: {operation}", operation=operation)

        if self.solver is None:
            self.logger.warning("Solver is None, skipping internal call")
            return

        if self.analysis is None:
            self.logger.warning("Analysis instance is None, skipping interprocedural analysis")
            return

        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping internal call")
            return

        function = operation.function
        if not isinstance(function, Function):
            self.logger.debug("Internal call function is not a Function instance, skipping")
            return

        # Delegate to the central interprocedural analyzer
        analyzer = InterproceduralAnalyzer(
            solver=self.solver,
            analysis=self.analysis,
            call_type_label="internal",
        )
        analyzer.analyze_call(operation, domain)
