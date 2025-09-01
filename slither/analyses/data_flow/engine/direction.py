from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from slither.core.cfg.node import Node


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
    ):
        pass


class Forward(Direction):
    def __init__(self):
        pass

    @property
    def IS_FORWARD(self) -> bool:
        return True

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: Deque[Node],
        global_state: Dict[int, "AnalysisState[A]"],
    ):
        # Apply transfer function to current node
        for operation in node.irs or [None]:
            analysis.transfer_function(node=node, domain=current_state.pre, operation=operation)

        # Set post state
        global_state[node.node_id].post = current_state.pre

        # Propagate to all successors
        for successor in node.sons:
            if successor and successor.node_id in global_state:
                son_state = global_state[successor.node_id]
                if son_state.pre.join(current_state.pre) and successor not in worklist:
                    worklist.append(successor)


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
    ):
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
