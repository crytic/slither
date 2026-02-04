"""Direction classes for forward and backward data flow analysis.

The direction determines how the analysis traverses the CFG and
propagates abstract states between nodes.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict, Optional

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations.condition import Condition


class Direction(ABC):
    """Abstract base class for analysis direction.

    Concrete subclasses implement forward or backward traversal
    of the control flow graph during fixpoint computation.
    """

    @property
    @abstractmethod
    def IS_FORWARD(self) -> bool:
        """Return True for forward analysis, False for backward."""

    @abstractmethod
    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Apply transfer function and propagate state to successors/predecessors.

        Args:
            analysis: The analysis providing the transfer function.
            current_state: The state at the current node.
            node: The CFG node being processed.
            worklist: Queue of nodes to process.
            global_state: Mapping from node IDs to analysis states.
        """


class Forward(Direction):
    """Forward data flow analysis direction.

    Propagates information from entry to exit, following CFG edges.
    Used for analyses like reaching definitions and interval analysis.
    """

    def __init__(self) -> None:
        """Initialize forward direction."""

    @property
    def IS_FORWARD(self) -> bool:
        """Return True indicating forward analysis."""
        return True

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        # Apply transfer function to current node
        condition_op: Optional[Condition] = None
        for operation in node.irs_ssa or [None]:
            analysis.transfer_function(node=node, domain=current_state.pre, operation=operation)
            # Track the Condition operation if present
            if isinstance(operation, Condition):
                condition_op = operation

        # Set post state
        global_state[node.node_id].post = current_state.pre

        # Check if this is a conditional node with exactly 2 successors
        is_conditional = (
            node.type in (NodeType.IF, NodeType.IFLOOP)
            and condition_op is not None
            and len(node.sons) == 2
        )

        # Propagate to successors with condition filtering if applicable
        for i, successor in enumerate(node.sons):
            if not successor or successor.node_id not in global_state:
                continue

            son_state = global_state[successor.node_id]

            # Detect back edge: propagating to a loop header (IFLOOP)
            is_back_edge = successor.type == NodeType.IFLOOP

            if is_conditional:
                # sons[0] is then branch, sons[1] is else branch
                branch_taken = i == 0
                filtered_domain = analysis.apply_condition(
                    current_state.pre, condition_op, branch_taken
                )
                # Widen on back edges before joining
                if is_back_edge:
                    filtered_domain = analysis.apply_widening(
                        filtered_domain, son_state.pre, set()
                    )
                changed = son_state.pre.join(filtered_domain)
            else:
                state_to_propagate = current_state.pre
                # Widen on back edges before joining
                if is_back_edge:
                    state_to_propagate = analysis.apply_widening(
                        state_to_propagate, son_state.pre, set()
                    )
                changed = son_state.pre.join(state_to_propagate)

            if changed and successor not in worklist:
                worklist.append(successor)


class Backward(Direction):
    """Backward data flow analysis direction.

    Propagates information from exit to entry, following reverse CFG edges.
    Used for analyses like liveness and very busy expressions.
    """

    @property
    def IS_FORWARD(self) -> bool:
        """Return False indicating backward analysis."""
        return False

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Apply transfer function for backward analysis (not yet implemented)."""
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
