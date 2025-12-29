from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Deque, Dict, Optional

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState

from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations.condition import Condition


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
        condition_op: Optional[Condition] = None
        for operation in node.irs_ssa or [None]:
            analysis.transfer_function(node=node, domain=current_state.pre, operation=operation)
            # Track the Condition operation if present
            if isinstance(operation, Condition):
                condition_op = operation

        # Set post state
        global_state[node.node_id].post = current_state.pre

        # Check if this is a conditional node with exactly 2 successors
        is_conditional = (
            node.type in (NodeType.IF, NodeType.IFLOOP)
            and condition_op is not None
            and len(node.sons) == 2
        )

        # Propagate to successors with condition filtering if applicable
        for i, successor in enumerate[Node](node.sons):
            if not successor or successor.node_id not in global_state:
                continue

            son_state = global_state[successor.node_id]

            if is_conditional:
                # sons[0] is then branch, sons[1] is else branch
                branch_taken = i == 0
                filtered_domain = analysis.apply_condition(
                    current_state.pre, condition_op, branch_taken
                )
                changed = son_state.pre.join(filtered_domain)
            else:
                # Non-conditional node: propagate without filtering
                changed = son_state.pre.join(current_state.pre)

            if changed and successor not in worklist:
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
