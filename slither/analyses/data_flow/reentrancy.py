from typing import List, Optional, Set
from enum import Enum, auto

from slither.analyses.data_flow.analysis import Analysis
from slither.analyses.data_flow.direction import Direction, Forward
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations import Call, EventCall, Operation


class ReentrancyInfo:
    def __init__(
        self,
        external_calls: Set[Call] = None,
        storage_variables_read: Set[Variable] = None,
        storage_variables_written: Set[Variable] = None,
        storage_variables_read_before_calls: Set[Variable] = None,
        events: Set[EventCall] = None,
    ):
        self.external_calls = external_calls or set()
        self.storage_variables_read = storage_variables_read or set()
        self.storage_variables_written = storage_variables_written or set()
        self.storage_variables_read_before_calls = storage_variables_read_before_calls or set()
        self.events = events or set()


class DomainVariant(Enum):
    BOTTOM = auto()
    TOP = auto()
    STATE = auto()


class ReentrancyDomain(Domain):
    def __init__(self, variant: DomainVariant, state: Optional[ReentrancyInfo] = None):
        self.variant = variant
        self.state = state

    @classmethod
    def bottom(cls) -> "ReentrancyDomain":
        return cls(DomainVariant.BOTTOM)

    @classmethod
    def top(cls) -> "ReentrancyDomain":
        return cls(DomainVariant.TOP)

    @classmethod
    def state(cls, info: ReentrancyInfo) -> "ReentrancyDomain":
        return cls(DomainVariant.STATE, info)

    def join(self, other: "ReentrancyDomain") -> bool:
        match self.variant, other.variant:
            case DomainVariant.TOP, _:
                return False
            case _, DomainVariant.BOTTOM:
                return False
            case DomainVariant.STATE, DomainVariant.STATE:
                if self.state == other.state:
                    return False
                self.state.external_calls.union(other.state.external_calls)
                self.state.storage_variables_read.union(other.state.storage_variables_read)
                self.state.storage_variables_read_before_calls.union(other.state.storage_variables_read_before_calls)
            case DomainVariant.BOTTOM, DomainVariant.STATE:
                self.state = other.state
            case _:
                self.variant = DomainVariant.TOP
        return True


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
        print(f"{node.expression} -- {operation}")
