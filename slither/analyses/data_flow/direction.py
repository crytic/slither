from abc import ABC, abstractmethod
from slither.core.cfg.node import Node
from typing import List


class Direction(ABC):
    @property
    @abstractmethod
    def IS_FORWARD(self) -> bool:
        pass

    @abstractmethod
    def apply_transfer_function(self, nodes: List[Node]):
        pass


class Forward(Direction):
    @property
    def IS_FORWARD(self) -> bool:
        return True

    def apply_transfer_function(self, nodes: List[Node]):
        raise NotImplementedError("Forward transfer function hasn't been developed yet")


class Backward(Direction):
    @property
    def IS_FORWARD(self) -> bool:
        return False

    def apply_transfer_function(self, nodes: List[Node]):
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
