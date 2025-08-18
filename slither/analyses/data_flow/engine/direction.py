from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING, Deque, Dict, List, Optional, Set, Union

if TYPE_CHECKING:

    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.declarations import Contract


from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function import Function
from slither.slithir.operations.binary import Binary, BinaryType


class Direction(ABC):
    @property
    @abstractmethod
    def IS_FORWARD(self) -> bool:
        pass

    @abstractmethod
    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        functions: List[Function],
    ):
        pass


class Forward(Direction):
    def __init__(self):
        self._numeric_literals_extracted = False
        self._loop_iteration_counts: Dict[int, int] = {}
        self._loop_previous_states: Dict[int, Domain] = {}  # Track previous state for each loop
        self._set_b_cardinality: int = 0
        self._set_b: Set[int] = set()

    @property
    def IS_FORWARD(self) -> bool:
        return True

    def _extract_condition(self, node: Node) -> Optional[Binary]:
        """Extract comparison condition from IF node."""
        if node.type != NodeType.IF:
            return None

        for operation in node.irs or []:
            if isinstance(operation, Binary) and operation.type in [
                BinaryType.GREATER,
                BinaryType.GREATER_EQUAL,
                BinaryType.LESS,
                BinaryType.LESS_EQUAL,
                BinaryType.EQUAL,
                BinaryType.NOT_EQUAL,
            ]:
                return operation
        return None

    def _is_bottom_domain(self, domain: Domain) -> bool:
        """Check if the domain is BOTTOM (unreachable state)."""
        return (
            hasattr(domain, "variant")
            and hasattr(domain.variant, "name")
            and domain.variant.name == "BOTTOM"
        )

    def _handle_ifloop_node(
        self,
        node: Node,
        current_state: "AnalysisState",
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        analysis: "Analysis",
    ) -> bool:
        """Handle IFLOOP nodes with iteration limiting."""
        if node.type != NodeType.IFLOOP:
            return False

        loop_id = node.node_id
        current_iteration = self._loop_iteration_counts.setdefault(loop_id, 0)

        # Check if we've exceeded maximum iterations (allow more iterations for widening to converge)
        max_iterations = max(
            self._set_b_cardinality * 3, 10
        )  # Allow more iterations for convergence
        if current_iteration >= max_iterations:
            self._exit_loop(node, current_state.pre, worklist, global_state, loop_id)
            return True

        # Handle state tracking and widening
        if current_iteration == 0:
            # First iteration: save current state as previous
            self._loop_previous_states[loop_id] = current_state.pre.deep_copy()
        else:
            # Apply widening with previous state on every iteration after the first
            print(f"Widening iteration {current_iteration} with previous state")
            previous_state = self._loop_previous_states[loop_id]
            widened_state = analysis.apply_widening(current_state.pre, previous_state, self._set_b)
            current_state.pre = widened_state

            # Check for convergence (if state hasn't changed significantly)
            if self._has_converged(previous_state, current_state.pre):
                print(f"🔄 Widening converged after {current_iteration} iterations")
                self._exit_loop(node, current_state.pre, worklist, global_state, loop_id)
                return True

            # Update previous state for next iteration
            self._loop_previous_states[loop_id] = current_state.pre.deep_copy()

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
            self._propagate_to_successor(node, node.sons[1], state, worklist, global_state)
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
            self._propagate_to_successor(node, node.sons[0], state, worklist, global_state)

    def _propagate_to_successor(
        self,
        node: Node,
        successor: Node,
        filtered_state: Domain,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Propagate state to a single successor."""
        if not successor or successor.node_id not in global_state:
            return

        # Skip unreachable branches
        if self._is_bottom_domain(filtered_state):
            self._handle_unreachable_branch(successor, filtered_state, worklist, global_state)
            return

        # Join states and update worklist
        son_state = global_state[successor.node_id]
        if son_state.pre.join(filtered_state) and successor not in worklist:
            worklist.append(successor)

    def _handle_unreachable_branch(
        self,
        successor: Node,
        bottom_state: Domain,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Handle propagation to unreachable branches."""

        # Remove from worklist (except ENDIF nodes)
        if successor in worklist and successor.type != NodeType.ENDIF:
            worklist.remove(successor)

        # Mark as unreachable
        global_state[successor.node_id].pre = bottom_state

    def _propagate_conditional(
        self,
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

        true_successor, false_successor = node.sons[0], node.sons[1]

        # Apply conditions and propagate
        true_state = analysis.apply_condition(current_state.pre, condition, True)
        false_state = analysis.apply_condition(current_state.pre, condition, False)

        self._propagate_to_successor(node, true_successor, true_state, worklist, global_state)
        self._propagate_to_successor(node, false_successor, false_state, worklist, global_state)

    def _propagate_regular(
        self,
        node: Node,
        current_state: "AnalysisState",
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> None:
        """Handle regular (non-conditional) propagation."""
        for successor in node.sons:
            self._propagate_to_successor(node, successor, current_state.pre, worklist, global_state)

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        functions: List[Function],
    ):

        # Apply transfer function to current node
        for operation in node.irs or [None]:
            analysis.transfer_function(
                node=node, domain=current_state.pre, operation=operation, functions=functions
            )

        # Set post state
        global_state[node.node_id].post = current_state.pre

        # Handle IFLOOP nodes specially
        if self._handle_ifloop_node(node, current_state, worklist, global_state, analysis):
            return

        # Handle propagation based on node type
        condition = self._extract_condition(node)
        if condition and len(node.sons) >= 2:
            self._propagate_conditional(
                node, current_state, condition, analysis, worklist, global_state
            )
        else:
            self._propagate_regular(node, current_state, worklist, global_state)

    def _has_converged(self, previous_state: "Domain", current_state: "Domain") -> bool:
        """Check if the widening has converged by comparing states."""
        # Simple convergence check: if states are equal, we've converged
        return previous_state == current_state


class Backward(Direction):
    @property
    def IS_FORWARD(self) -> bool:
        return False

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        functions: List[Function],
    ):
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
