"""Abstract domain interface for data flow analysis.

Defines the lattice structure required for fixpoint computation.
"""

from abc import ABC, abstractmethod


class Domain(ABC):
    """Abstract base class for data flow analysis domains.

    A domain represents the abstract values computed during analysis.
    It forms a lattice with top, bottom, and join operations.
    Concrete subclasses implement specific abstract domains like
    intervals, signs, or pointer analysis.
    """

    @abstractmethod
    def top(cls) -> "Domain":
        """Return the top element of the domain (least informative)."""

    @abstractmethod
    def bottom(cls) -> "Domain":
        """Return the bottom element of the domain (most informative)."""

    @abstractmethod
    def join(self, other: "Domain") -> bool:
        """Compute the least upper bound of this element and another.

        Updates self in-place with the join result.

        Args:
            other: The domain element to join with.

        Returns:
            True if self changed as a result of the join.
        """
