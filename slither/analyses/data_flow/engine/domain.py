from abc import ABC, abstractmethod
from typing import Self


class Domain(ABC):
    @abstractmethod
    def top(cls) -> Self:
        """The top element of the domain"""
        pass

    @abstractmethod
    def bottom(cls) -> Self:
        """The bottom element of the domain"""
        pass

    @abstractmethod
    def join(self, other: Self) -> bool:
        """Computes the least upper bound of two elements and store the result in self.
        Return True if self changed."""
        pass
