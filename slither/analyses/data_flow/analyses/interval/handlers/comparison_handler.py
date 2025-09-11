from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary


class ComparisonHandler:
    def handle_comparison(self, node: Node, domain: IntervalDomain, operation: Binary):
        pass
