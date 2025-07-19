from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict, List, Optional

if TYPE_CHECKING:
    from slither.analyses.data_flow.analysis import Analysis, AnalysisState, A

from loguru import logger
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.function import Function
from slither.slithir.operations.binary import Binary, BinaryType
from slither.analyses.data_flow.domain import Domain


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
        # Apply transfer function to current node
        for operation in node.irs or [None]:
            analysis.transfer_function(
                node=node, domain=current_state.pre, operation=operation, functions=functions
            )

        # Set post state
        global_state[node.node_id].post = current_state.pre

        # Propagate to successors
        condition = self._extract_condition(node)

        if condition:
            true_successor = node.sons[0]
            false_successor = node.sons[1]

            # Apply true condition
            true_state = analysis.apply_condition(current_state.pre, condition, True)
            self._propagate_to_successor(node, true_successor, true_state, worklist, global_state)

            # Apply false condition
            false_state = analysis.apply_condition(current_state.pre, condition, False)
            self._propagate_to_successor(node, false_successor, false_state, worklist, global_state)

        else:
            # Regular propagation for non-conditional nodes
            for successor in node.sons:
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
