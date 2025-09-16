from typing import TYPE_CHECKING, Deque, Dict

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from loguru import logger
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary


class PropagationManager:
    """Manages state propagation for data flow analysis."""

    @staticmethod
    def propagate_to_successor(
        node: Node,
        successor: Node,
        state_to_propagate,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Propagate state to a single successor."""
        if not successor or successor.node_id not in global_state:
            return

        # Skip unreachable branches
        if state_to_propagate.is_bottom():
            logger.info(
                f"🚫 Skipping propagation to node {successor.node_id} - BOTTOM domain (unreachable branch)"
            )
            return

        # Join states and update worklist
        successor_state = global_state[successor.node_id]
        if successor_state.pre.join(state_to_propagate) and successor not in worklist:
            worklist.append(successor)

    @staticmethod
    def propagate_conditional(
        node: Node,
        current_state: "AnalysisState",
        condition: Binary,
        analysis: "Analysis",
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Handle conditional propagation for IF nodes."""
        if len(node.sons) < 2:
            return

        then_successor, else_successor = node.sons[0], node.sons[1]

        # Apply conditions and propagate
        then_state = analysis.apply_condition(current_state.pre, condition, True)
        else_state = analysis.apply_condition(current_state.pre, condition, False)

        PropagationManager.propagate_to_successor(
            node, then_successor, then_state, worklist, global_state
        )
        PropagationManager.propagate_to_successor(
            node, else_successor, else_state, worklist, global_state
        )

    @staticmethod
    def propagate_unconditional(
        node: Node,
        current_state: "AnalysisState",
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Handle unconditional (non-conditional) propagation."""
        for successor in node.sons:
            PropagationManager.propagate_to_successor(
                node, successor, current_state.pre, worklist, global_state
            )
