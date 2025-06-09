from abc import ABC, abstractmethod
from slither.analyses.data_flow.direction import Direction
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from typing import TypeVar, Generic

class Analysis(ABC):
    @abstractmethod
    def domain(self) -> Domain:
        pass

    @abstractmethod
    def direction(self) -> Direction:
        pass

    @abstractmethod
    def transfer_function(self, node: Node):
        pass

    @abstractmethod
    def bottom_value(self) -> Domain:
        pass

A = TypeVar('A', bound=Analysis)

class AnalysisState(Generic[A]):
    def __init__(self, pre: Domain, post: Domain) -> None:
        self.pre: Domain = pre
        self.post: Domain = post