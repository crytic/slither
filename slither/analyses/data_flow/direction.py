from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict, List

if TYPE_CHECKING:
    from slither.analyses.data_flow.analysis import Analysis, AnalysisState, A

from slither.core.cfg.node import Node
from slither.core.declarations.function import Function


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
        node_to_index: Dict[Node, int],
    ):
        pass


class Forward(Direction):

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
        functions: List[Function],
        node_to_index: Dict[Node, int],
    ):
        for operation in node.irs:
            analysis.transfer_function(
                node=node, domain=current_state.pre, operation=operation, functions=functions
            )
        return
        node_index = node_to_index[node]
        global_state[node_index].post = current_state.pre # set the post state of the current block

        for son in node.sons: #propagate
            son_index = node_to_index[son]
            if son_index not in global_state:
                continue
            son_state = global_state[son_index]
            changed = son_state.pre.join(current_state.pre)

            if not changed:
                continue

            if son in worklist:
                continue

            worklist.append(son)


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
        node_to_index: Dict[Node, int],
    ):
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
