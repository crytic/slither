from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from slither.analyses.data_flow.direction import Direction
from slither.analyses.data_flow.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.slithir.operations.operation import Operation


class Analysis(ABC):
    @abstractmethod
    def domain(self) -> Domain:
        pass

    @abstractmethod
    def direction(self) -> Direction:
        pass

    @abstractmethod
    def transfer_function(
        self, node: Node, domain: Domain, operation: Operation, functions: List[Function]
    ):
        pass

    @abstractmethod
    def bottom_value(self) -> Domain:
        pass

    def apply_condition(self, domain: Domain, condition: Operation, branch_taken: bool) -> Domain:
        """Override this to handle branch filtering. Default: no-op"""
        return domain  # Analyses that don't implement this get no filtering

    def apply_widening(self, current_state: Domain, previous_state: Domain, set_b: set) -> Domain:
        """Override this to implement widening operations. Default: no-op"""
        return current_state  # Analyses that don't implement this get no widening


A = TypeVar("A", bound=Analysis)


class AnalysisState(Generic[A]):
    def __init__(self, pre: Domain, post: Domain) -> None:
        self.pre: Domain = pre
        self.post: Domain = post
