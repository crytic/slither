from typing import TYPE_CHECKING, Deque, Dict, Set

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from loguru import logger
from slither.core.cfg.node import Node, NodeType
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.engine.propagation_manager import PropagationManager


class LoopManager:
    """Manages loop handling for data flow analysis with widening operations."""

    def __init__(self):
        self._widening_literals_extracted = False
        self._loop_iteration_counts: Dict[int, int] = {}
        self._loop_previous_states: Dict[int, Domain] = {}  # Track previous state for each loop
        self._widening_literals_count: int = 0
        self._widening_literals: Set[int] = set()

    def handle_loop_node(
        self,
        node: Node,
        current_state: "AnalysisState",
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        analysis: "Analysis",
    ) -> bool:
        """Handle IFLOOP nodes with iteration limiting and widening operations."""
        if node.type != NodeType.IFLOOP:
            return False

        # Ensure widening literals are extracted for this analysis
        self._ensure_widening_literals_extracted()

        loop_node_id = node.node_id
        current_iteration_count = self._loop_iteration_counts.setdefault(loop_node_id, 0)

        # Check if we've exceeded maximum iterations (allow more iterations for widening to converge)
        max_widening_iterations = max(
            self._widening_literals_count * 3, 10
        )  # Allow more iterations for convergence
        if current_iteration_count >= max_widening_iterations:
            self._exit_loop_iteration(node, current_state.pre, worklist, global_state, loop_node_id)
            return True

        # Handle state tracking and widening
        if current_iteration_count == 0:
            # First iteration: save current state as previous for widening
            self._loop_previous_states[loop_node_id] = current_state.pre.deep_copy()
        else:
            # Apply widening with previous state on every iteration after the first
            logger.debug(f"Widening iteration {current_iteration_count} with previous state")
            previous_loop_state = self._loop_previous_states[loop_node_id]
            widened_state = analysis.apply_widening(
                current_state.pre, previous_loop_state, self._widening_literals
            )
            current_state.pre = widened_state

            # Check for convergence (if state hasn't changed significantly)
            if self._has_widening_converged(previous_loop_state, current_state.pre):
                logger.debug(f"🔄 Widening converged after {current_iteration_count} iterations")
                self._exit_loop_iteration(
                    node, current_state.pre, worklist, global_state, loop_node_id
                )
                return True

            # Update previous state for next iteration
            self._loop_previous_states[loop_node_id] = current_state.pre.deep_copy()

        # Continue loop iteration
        self._continue_loop_iteration(node, current_state.pre, worklist, global_state, loop_node_id)
        return True

    def _exit_loop_iteration(
        self,
        node: Node,
        state: Domain,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        loop_node_id: int,
    ) -> None:
        """Exit loop iteration by propagating to exit node and resetting counter."""
        if len(node.sons) > 1:
            PropagationManager.propagate_to_successor(
                node, node.sons[1], state, worklist, global_state
            )
        self._loop_iteration_counts[loop_node_id] = 0
        # Clear previous state when exiting loop
        if loop_node_id in self._loop_previous_states:
            del self._loop_previous_states[loop_node_id]

    def _continue_loop_iteration(
        self,
        node: Node,
        state: Domain,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        loop_node_id: int,
    ) -> None:
        """Continue loop iteration by propagating to body node and incrementing counter."""
        self._loop_iteration_counts[loop_node_id] += 1
        if node.sons:
            PropagationManager.propagate_to_successor(
                node, node.sons[0], state, worklist, global_state
            )

    def _ensure_widening_literals_extracted(self) -> None:
        """Extract widening literals once at the beginning of analysis."""
        if self._widening_literals_extracted:
            return

        try:
            # Use default widening literals since we don't have access to the function
            self._widening_literals = {0, 1, -1, 2, 10, 100, 1000}
            self._widening_literals_count = len(self._widening_literals)

        except Exception as e:
            logger.warning(f"Failed to extract widening literals: {e}")
        finally:
            self._widening_literals_extracted = True

    def _has_widening_converged(self, previous_state: "Domain", current_state: "Domain") -> bool:
        """Check if the widening has converged by comparing states."""
        # Simple convergence check: if states are equal, we've converged
        return previous_state == current_state

    def reset_for_new_analysis(self) -> None:
        """Reset loop manager state for new analysis."""
        self._widening_literals_extracted = False
        self._loop_iteration_counts.clear()
        self._loop_previous_states.clear()
        self._widening_literals_count = 0
        self._widening_literals.clear()
