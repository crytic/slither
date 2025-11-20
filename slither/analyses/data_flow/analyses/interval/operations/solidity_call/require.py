from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.core.cfg.node import Node
from slither.slithir.operations.solidity_call import SolidityCall


class RequireHandler(BaseOperationHandler):
    """Handler for require calls."""

    def handle(self, operation: SolidityCall, domain: IntervalDomain, node: Node) -> None:
        self.logger.debug("Handling require call: {operation}", operation=operation)
        pass
