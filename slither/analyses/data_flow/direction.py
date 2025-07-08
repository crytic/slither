from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict, List

if TYPE_CHECKING:
    from slither.analyses.data_flow.analysis import Analysis, AnalysisState, A

from loguru import logger
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
    ):
        for operation in node.irs or [None]:
            analysis.transfer_function(
                node=node, domain=current_state.pre, operation=operation, functions=functions
            )
        # Original code. Ignores unintialized variables since no operations exist.
        # for operation in node.irs:
        #     analysis.transfer_function(
        #         node=node, domain=current_state.pre, operation=operation, functions=functions
        #     )

        global_state[node.node_id].post = (
            current_state.pre
        )  # set the post state of the current block

        for son in node.sons:  # propagate
            if not son:
                continue
            if son.node_id not in global_state:
                continue
            son_state = global_state[son.node_id]

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
    ):
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
