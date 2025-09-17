from typing import TYPE_CHECKING, Deque, Dict, Set

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from loguru import logger
from slither.core.cfg.node import Node, NodeType
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.engine.propagation_manager import PropagationManager
from slither.analyses.data_flow.engine.widening_literal_extractor import (
    extract_numeric_literals_for_function,
)


class LoopManager:
    """Manages loop handling for data flow analysis with widening operations."""

    def __init__(self):
        self._numeric_literals_extracted = False
        self._loop_iteration_counts: Dict[int, int] = {}
        self._loop_previous_states: Dict[int, Domain] = {}  # Track previous state for each loop
        self._widening_literals_cardinality: int = 0
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

        # Ensure numeric literals are extracted for this analysis
        self._ensure_widening_literals_extracted(node.function)

        loop_id = node.node_id
        current_iteration = self._loop_iteration_counts.setdefault(loop_id, 0)

        # Check if we've exceeded maximum iterations (widening should converge in |B| iterations)
        max_iterations = (
            self._widening_literals_cardinality
        )  # Widening should converge in |B| iterations
        if current_iteration >= max_iterations:
            self._exit_loop(node, current_state.pre, worklist, global_state, loop_id)
            return True

        # Handle state tracking and widening
        if current_iteration == 0:
            # First iteration: save current state as previous
            self._loop_previous_states[loop_id] = current_state.pre.deep_copy()
        else:
            # Apply widening with previous state on every iteration after the first
            logger.debug(f"Widening iteration {current_iteration} with previous state")
            previous_widened_state = self._loop_previous_states[loop_id]
            widened_state = analysis.apply_widening(
                current_state.pre, previous_widened_state, self._widening_literals
            )

            # Check for convergence (if widened state hasn't changed significantly)
            if self._has_converged(previous_widened_state, widened_state):
                logger.debug(f"🔄 Widening converged after {current_iteration} iterations")
                self._exit_loop(node, widened_state, worklist, global_state, loop_id)
                return True

            # Update current state and previous state for next iteration
            current_state.pre = widened_state
            self._loop_previous_states[loop_id] = widened_state.deep_copy()

        # Continue loop iteration
        self._continue_loop(node, current_state.pre, worklist, global_state, loop_id)
        return True

    def _exit_loop(
        self,
        node: Node,
        state: Domain,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        loop_id: int,
    ) -> None:
        """Exit loop by propagating to exit node and resetting counter."""
        if len(node.sons) > 1:
            PropagationManager.propagate_to_successor(
                node, node.sons[1], state, worklist, global_state
            )
        self._loop_iteration_counts[loop_id] = 0
        # Clear previous state when exiting loop
        if loop_id in self._loop_previous_states:
            del self._loop_previous_states[loop_id]

    def _continue_loop(
        self,
        node: Node,
        state: Domain,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        loop_id: int,
    ) -> None:
        """Continue loop by propagating to body node and incrementing counter."""
        self._loop_iteration_counts[loop_id] += 1
        if node.sons:
            PropagationManager.propagate_to_successor(
                node, node.sons[0], state, worklist, global_state
            )

    def _ensure_widening_literals_extracted(self, function) -> None:
        """Extract widening literals once at the beginning of analysis."""
        if self._numeric_literals_extracted:
            return

        try:
            # Extract widening literals from the function
            self._widening_literals, self._widening_literals_cardinality = (
                extract_numeric_literals_for_function(function)
            )
            logger.debug(
                f"🔍 Extracted literals for function {function.name}: {sorted(self._widening_literals)}"
            )

        except Exception as e:
            logger.warning(f"Failed to extract numeric literals: {e}")
        finally:
            self._numeric_literals_extracted = True

    def _has_converged(self, previous_state: "Domain", current_state: "Domain") -> bool:
        """Check if the widening has converged by comparing states."""
        # Simple convergence check: if states are equal, we've converged
        return previous_state == current_state

    def reset_for_new_analysis(self) -> None:
        """Reset loop manager state for new analysis."""
        self._numeric_literals_extracted = False
        self._loop_iteration_counts.clear()
        self._loop_previous_states.clear()
        self._widening_literals_cardinality = 0
        self._widening_literals.clear()
