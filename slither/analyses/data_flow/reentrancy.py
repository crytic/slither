from typing import List

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.slithir.operations.operation import Operation


class ReentrancyDomain(Domain):

    @classmethod
    def top(cls) -> "ReentrancyDomain":
       return cls()

    @classmethod
    def bottom(cls) -> "ReentrancyDomain":
        return cls()

    def join(self, other: "ReentrancyDomain") -> bool:
        return False


class ReentrancyAnalysis(Analysis):
    def __init__(self):
        self._direction = Forward()

    def domain(self) -> Domain:
        return ReentrancyDomain()

    def direction(self) -> Direction:
        return self._direction

    def bottom_value(self) -> Domain:
        return ReentrancyDomain.bottom()

    def transfer_function(self, node: Node, domain: Domain, operation: Operation, functions: List[Function]):
        print(node.expression)