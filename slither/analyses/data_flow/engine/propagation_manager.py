from typing import TYPE_CHECKING, Deque, Dict

from slither.core.variables.variable import Variable

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

        if not successor or successor.node_id not in global_state:
            return

        # Skip unreachable branches
        if state_to_propagate.is_bottom():
            return

        # Skip unreachable branches (TOP domain)
        if state_to_propagate.variant == DomainVariant.TOP:
            # Only mark as unreachable if it hasn't been processed through a reachable path
            successor_state = global_state[successor.node_id]
            if successor_state.pre.variant == DomainVariant.BOTTOM:
                # Only mark as unreachable if it's still uninitialized
                successor_state.pre = state_to_propagate
                successor_state.post = state_to_propagate
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
        condition_variable: Variable,
    ) -> None:
        """Handle conditional propagation for IF nodes."""
        if len(node.sons) < 2:
            return

        then_successor, else_successor = node.sons[0], node.sons[1]

        # Apply conditions and propagate
        then_state = analysis.apply_condition(current_state.pre, condition, True, condition_variable)
        else_state = analysis.apply_condition(current_state.pre, condition, False, condition_variable)

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
