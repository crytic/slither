from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from slither.analyses.data_flow.engine.direction import Direction
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.operation import Operation


class Analysis(ABC):
    @abstractmethod
    def domain(self) -> Domain:
        pass

    @abstractmethod
    def direction(self) -> Direction:
        pass

    @abstractmethod
    def transfer_function(self, node: Node, domain: Domain, operation: Operation):
        pass

    @abstractmethod
    def bottom_value(self) -> Domain:
        pass

    def apply_condition(self, domain: Domain, condition: Condition, branch_taken: bool) -> Domain:
        """Apply branch-specific constraints based on condition. Override to implement filtering."""
        return domain  # Analyses that don't implement this get no filtering

    def apply_widening(self, current_state: Domain, previous_state: Domain, set_b: set) -> Domain:
        """Override this to implement widening operations. Default: no-op"""
        return current_state  # Analyses that don't implement this get no widening


A = TypeVar("A", bound=Analysis)


class AnalysisState(Generic[A]):
    def __init__(self, pre: Domain, post: Domain) -> None:
        self.pre: Domain = pre
        self.post: Domain = post
