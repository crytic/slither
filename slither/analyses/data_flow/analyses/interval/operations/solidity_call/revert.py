from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.core.cfg.node import Node
from slither.slithir.operations.solidity_call import SolidityCall


class RevertHandler(BaseOperationHandler):
    """Handler for revert calls.

    Unlike require() and assert(), revert() is unconditional and always reverts.
    The path after a revert is always unreachable, so we set the domain to TOP.
    """

    def handle(self, operation: SolidityCall, domain: IntervalDomain, node: Node) -> None:
        self.logger.debug("Handling revert call: {operation}", operation=operation)

        # Skip if domain is not in STATE variant
        if domain.variant != DomainVariant.STATE:
            self.logger.debug("Domain is not in STATE variant, skipping revert")
            return

        # revert() always reverts unconditionally, marking the path as unreachable
        domain.variant = DomainVariant.TOP
        self.logger.debug("Revert call encountered, setting domain to TOP (unreachable path)")
