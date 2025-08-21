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
        functions: List[Function],
    ):
        # Apply transfer function to current node
        for operation in node.irs or [None]:
            analysis.transfer_function(
                node=node, domain=current_state.pre, operation=operation, functions=functions
            )

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
        functions: List[Function],
    ):
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
