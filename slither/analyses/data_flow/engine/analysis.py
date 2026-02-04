"""Abstract analysis interface for data flow analysis.

Defines the interface that concrete analyses must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from slither.analyses.data_flow.engine.direction import Direction
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.slithir.operations.condition import Condition
from slither.slithir.operations.operation import Operation

if TYPE_CHECKING:
    from slither.core.declarations.function import Function


class Analysis(ABC):
    """Abstract base class for data flow analyses.

    Concrete analyses implement domain-specific logic by providing:
    - A domain type for abstract values
    - A direction (forward or backward)
    - Transfer functions for IR operations
    """

    @abstractmethod
    def domain(self) -> Domain:
        """Return an instance of the domain for this analysis."""

    @abstractmethod
    def direction(self) -> Direction:
        """Return the analysis direction (Forward or Backward)."""

    @abstractmethod
    def transfer_function(self, node: Node, domain: Domain, operation: Operation) -> None:
        """Apply the transfer function for an IR operation.

        Args:
            node: The CFG node containing the operation.
            domain: The current abstract state to update in-place.
            operation: The SlithIR operation to process.
        """

    @abstractmethod
    def bottom_value(self) -> Domain:
        """Return the bottom value of the domain for initialization."""

    def apply_condition(
        self, domain: Domain, condition: Condition, branch_taken: bool
    ) -> Domain:
        """Apply branch-specific filtering based on a condition.

        Override to implement path-sensitive analysis that constrains
        the domain based on which branch is taken.

        Args:
            domain: The current abstract state.
            condition: The condition operation from the branch.
            branch_taken: True if then-branch, False if else-branch.

        Returns:
            The filtered domain for the taken branch.
        """
        return domain

    def apply_widening(
        self, current_state: Domain, previous_state: Domain, widening_thresholds: set[int]
    ) -> Domain:
        """Apply widening to accelerate fixpoint convergence.

        Override to implement widening for analyses with infinite
        ascending chains.

        Args:
            current_state: The state after the current iteration.
            previous_state: The state from the previous iteration.
            widening_thresholds: Set of threshold values for widening.

        Returns:
            The widened state.
        """
        return current_state

    def prepare_for_function(self, function: "Function") -> None:
        """Prepare analysis for a specific function.

        Called by Engine.new after function is set. Override to collect
        function-specific data like widening thresholds.

        Args:
            function: The function about to be analyzed.
        """


A = TypeVar("A", bound=Analysis)


class AnalysisState(Generic[A]):
    """Container for pre and post states at a CFG node.

    Attributes:
        pre: The abstract state before the node's operations.
        post: The abstract state after the node's operations.
    """

    def __init__(self, pre: Domain, post: Domain) -> None:
        """Initialize with pre and post states.

        Args:
            pre: Initial pre-state (typically bottom).
            post: Initial post-state (typically bottom).
        """
        self.pre: Domain = pre
        self.post: Domain = post
