from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.core.cfg.node import Node
from slither.slithir.operations.phi import Phi


class PhiHandler(BaseOperationHandler):
    """Handler for Phi operations."""

    def handle(self, operation: Phi, domain: IntervalDomain, node: Node) -> None:
        pass
