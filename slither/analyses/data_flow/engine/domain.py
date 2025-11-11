from abc import ABC, abstractmethod


class Domain(ABC):
    @abstractmethod
    def top(cls) -> "Domain":
        """The top element of the domain"""

    @abstractmethod
    def bottom(cls) -> "Domain":
        """The bottom element of the domain"""

    @abstractmethod
    def join(self, other: "Domain") -> bool:
        """Computes the least upper bound of two elements and store the result in self.
        Return True if self changed."""
