from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict, List, Optional, Set, Union

if TYPE_CHECKING:
    from slither.analyses.data_flow.analysis import Analysis, AnalysisState, A
    from slither.core.compilation_unit import SlitherCompilationUnit
    from slither.core.declarations import Contract

from loguru import logger
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function import Function
from slither.slithir.operations.binary import Binary, BinaryType
from slither.analyses.data_flow.domain import Domain
from slither.analyses.data_flow.numeric_literal_extractor import (
    extract_numeric_literals_with_summary,
)


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
        self._loop_iteration_counts: Dict[int, int] = {}  # Track iterations per IFLOOP node
        self._set_b_cardinality: int = 0  # Store |B| for loop control

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
        # Check if the domain has a variant attribute and if it's BOTTOM
        if hasattr(domain, "variant"):
            # Check by name to avoid importing specific implementations
            if hasattr(domain.variant, "name") and domain.variant.name == "BOTTOM":
                print("eureka")
                return True

        return False

    def _handle_ifloop_node(
        self,
        node: Node,
        current_state: "AnalysisState",
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ) -> bool:
        """Handle IFLOOP nodes to ensure exactly |B| iterations."""
        if node.type != NodeType.IFLOOP:
            return False

        loop_node_id = node.node_id

        # Initialize counter if not exists
        if loop_node_id not in self._loop_iteration_counts:
            self._loop_iteration_counts[loop_node_id] = 0

        current_iterations = self._loop_iteration_counts[loop_node_id]

        logger.info(
            f"🔄 IFLOOP node {loop_node_id}: iteration {current_iterations + 1}/{self._set_b_cardinality}"
        )

        if current_iterations < self._set_b_cardinality:
            # Continue loop: increment counter and go to loop body
            self._loop_iteration_counts[loop_node_id] += 1
            successor_node = node.sons[0] if node.sons else None
            action_msg = f"Continuing loop: node {loop_node_id}"
        else:
            # Exit loop: reset counter and go to loop exit
            self._loop_iteration_counts[loop_node_id] = 0  # Reset for potential re-entry
            logger.info(
                f"🔄 Exiting loop: node {loop_node_id} (completed {self._set_b_cardinality} iterations)"
            )
            successor_node = node.sons[1] if node.sons and len(node.sons) > 1 else None
            action_msg = f"Loop exit: node {loop_node_id}"

        # Propagate state to successor using existing method for consistency
        if successor_node:
            logger.info(f"🔄 {action_msg} → {successor_node.node_id}")
            self._propagate_to_successor(
                node, successor_node, current_state.pre, worklist, global_state
            )

        return True  # Handled IFLOOP

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

        # Check if the filtered state is BOTTOM (unreachable branch)
        if self._is_bottom_domain(filtered_state):
            logger.info(
                f"🚫 Skipping propagation to node {successor.node_id} - BOTTOM domain (unreachable branch)"
            )

            # Remove the successor from worklist
            if successor in worklist:
                if successor.type != NodeType.ENDIF:
                    worklist.remove(successor)
                    logger.info(f"🗑️ Removed node {successor.node_id} from worklist - unreachable")

            # Also mark successor's pre-state as BOTTOM to prevent future processing
            global_state[successor.node_id].pre = filtered_state  # This is BOTTOM
            return

        son_state = global_state[successor.node_id]

        # Join states and add to worklist if changed
        changed = son_state.pre.join(filtered_state)
        if changed and successor not in worklist:
            worklist.append(successor)

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
        functions: List[Function],
    ):
        # Extract numeric literals once at the beginning
        if not self._numeric_literals_extracted:
            try:
                # Get compilation unit from the first function
                if functions and hasattr(functions[0], "contract_declarer"):
                    contract_declarer: Contract = functions[0].contract_declarer
                    slither = contract_declarer.compilation_unit.core
                    set_b: Set[int]
                    cardinality: int
                    set_b, cardinality = extract_numeric_literals_with_summary(slither)
                    self._set_b_cardinality = cardinality  # Store |B| for loop control
                    logger.info(f"📊 Numeric literals extracted: {cardinality} literals found")
                    logger.info(f"📋 Set B: {sorted(set_b)}")
                    logger.info(f"🔄 Loop iteration limit set to |B| = {cardinality}")
                self._numeric_literals_extracted = True
            except Exception as e:
                logger.warning(f"Failed to extract numeric literals: {e}")
                self._numeric_literals_extracted = True

        # Apply transfer function to current node
        for operation in node.irs or [None]:
            logger.info(
                f"🔄 Applying transfer function to node {node.node_id} with operation: {operation}"
            )
            analysis.transfer_function(
                node=node, domain=current_state.pre, operation=operation, functions=functions
            )

        # Set post state
        global_state[node.node_id].post = current_state.pre

        # Check if this is an IFLOOP node and handle it specially
        if self._handle_ifloop_node(node, current_state, worklist, global_state):
            return  # IFLOOP handled, no need for regular propagation

        # Propagate to successors
        condition = self._extract_condition(node)

        if condition and len(node.sons) >= 2:
            true_successor = node.sons[0]
            false_successor = node.sons[1]
            # Apply true condition
            true_state = analysis.apply_condition(current_state.pre, condition, True)

            # Propagate to true successor (will be skipped if BOTTOM)
            self._propagate_to_successor(node, true_successor, true_state, worklist, global_state)

            # Apply false condition
            false_state = analysis.apply_condition(current_state.pre, condition, False)

            # Propagate to false successor (will be skipped if BOTTOM)
            self._propagate_to_successor(node, false_successor, false_state, worklist, global_state)

        else:
            # Regular propagation for non-conditional nodes
            for successor in node.sons:
                if successor.node_id == 5:
                    print(f"Node 5 is successor of node {node.node_id}")
                self._propagate_to_successor(
                    node, successor, current_state.pre, worklist, global_state
                )


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
