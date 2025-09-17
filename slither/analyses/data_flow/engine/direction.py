from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from slither.core.cfg.node import Node
from slither.slithir.operations.binary import Binary

from slither.analyses.data_flow.engine.node_analyzer import NodeAnalyzer
from slither.analyses.data_flow.engine.propagation_manager import PropagationManager
from slither.analyses.data_flow.engine.loop_manager import LoopManager


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
        self._loop_manager = LoopManager()

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

        # Handle IFLOOP nodes specially using LoopManager
        if self._loop_manager.handle_loop_node(
            node, current_state, worklist, global_state, analysis
        ):
            return

        # Handle propagation based on node type
        condition = NodeAnalyzer.extract_condition(node)
        if condition and NodeAnalyzer.is_conditional_node(node):
            PropagationManager.propagate_conditional(
                node, current_state, condition, analysis, worklist, global_state
            )
        else:
            PropagationManager.propagate_unconditional(node, current_state, worklist, global_state)


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
