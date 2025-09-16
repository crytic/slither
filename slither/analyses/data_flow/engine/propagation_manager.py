from typing import TYPE_CHECKING, Deque, Dict

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from loguru import logger
from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary
from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant


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
        # Debug Node 4 propagation
        if successor and successor.node_id == 4:
            logger.info(f"🔍 PROPAGATION TO NODE 4:")
            logger.info(f"   From node: {node.node_id} ({node.type})")
            logger.info(f"   State to propagate variant: {state_to_propagate.variant}")
            logger.info(f"   State is BOTTOM: {state_to_propagate.is_bottom()}")
            logger.info(f"   Successor in global_state: {successor.node_id in global_state}")

        if not successor or successor.node_id not in global_state:
            if successor and successor.node_id == 4:
                logger.info(f"🔍 NODE 4: Skipping propagation - successor not in global_state")
            return

        # Skip unreachable branches
        if state_to_propagate.is_bottom():
            logger.info(
                f"🚫 Skipping propagation to node {successor.node_id} - BOTTOM domain (unreachable branch)"
            )
            return

        # Skip unreachable branches (TOP domain)
        if state_to_propagate.variant == DomainVariant.TOP:
            logger.info(
                f"🚫 Skipping propagation to node {successor.node_id} - TOP domain (unreachable branch)"
            )
            # Only mark as unreachable if it hasn't been processed through a reachable path
            successor_state = global_state[successor.node_id]
            if successor_state.pre.variant == DomainVariant.BOTTOM:
                # Only mark as unreachable if it's still uninitialized
                successor_state.pre = state_to_propagate
                successor_state.post = state_to_propagate
            else:
                logger.info(
                    f"🔍 Node {successor.node_id} already processed through reachable path, keeping existing state"
                )
            return

        # Join states and update worklist
        successor_state = global_state[successor.node_id]
        if successor_state.pre.join(state_to_propagate) and successor not in worklist:
            if successor.node_id == 4:
                logger.info(f"🔍 NODE 4: Adding to worklist from node {node.node_id}")
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

        # Debug Node 4 in conditional propagation
        if node.node_id == 3:  # Node 3 is the if (x == 101) condition
            logger.info(f"🔍 CONDITIONAL PROPAGATION FROM NODE 3:")
            logger.info(f"   Condition: {condition}")
            logger.info(f"   Then successor: {then_successor.node_id} ({then_successor.type})")
            logger.info(f"   Else successor: {else_successor.node_id} ({else_successor.type})")
            logger.info(f"   Node 4 is then successor: {then_successor.node_id == 4}")
            logger.info(f"   Node 4 is else successor: {else_successor.node_id == 4}")

        # Debug outer condition (Node 1: x > 100)
        if node.node_id == 1:  # Node 1 is the if (x > 100) condition
            logger.info(f"🔍 CONDITIONAL PROPAGATION FROM NODE 1:")
            logger.info(f"   Condition: {condition}")
            logger.info(f"   Then successor: {then_successor.node_id} ({then_successor.type})")
            logger.info(f"   Else successor: {else_successor.node_id} ({else_successor.type})")

        # Apply conditions and propagate
        then_state = analysis.apply_condition(current_state.pre, condition, True)
        else_state = analysis.apply_condition(current_state.pre, condition, False)

        if node.node_id == 3:
            logger.info(
                f"🔍 NODE 3: Then state variant: {then_state.variant}, is_bottom: {then_state.is_bottom()}"
            )
            logger.info(
                f"🔍 NODE 3: Else state variant: {else_state.variant}, is_bottom: {else_state.is_bottom()}"
            )

        # Always propagate to then branch
        PropagationManager.propagate_to_successor(
            node, then_successor, then_state, worklist, global_state
        )

        # Only propagate to else branch if it's not unreachable
        if not else_state.is_bottom() and else_state.variant != DomainVariant.TOP:
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
