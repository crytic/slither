from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.core.cfg.node import Node
from slither.slithir.operations.return_operation import Return


class ReturnHandler(BaseOperationHandler):
    """Handler for return operations."""

    def handle(self, operation: Return, domain: IntervalDomain, node: Node) -> None:
        self.logger.debug("Handling return operation: {operation}", operation=operation)
        pass
