from typing import List, Set

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.event import Event
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.operation import Operation


class ReentrancyInfo:
    def __init__(
        self,
        external_calls: Set[Call] = None,
        storage_variables_read: Set[Variable] = None,
        storage_variables_written: Set[Variable] = None,
        storage_variables_read_before_calls: Set[Variable] = None,
        events: Set[Event] = None,
    ):
        self.external_calls = external_calls or set()
        self.storage_variables_read = storage_variables_read or set()
        self.storage_variables_written = storage_variables_written or set()
        self.storage_variables_read_before_calls = storage_variables_read_before_calls or set()
        self.events = events or set()


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

    def transfer_function(
        self, node: Node, domain: Domain, operation: Operation, functions: List[Function]
    ):
        print(node.expression)
