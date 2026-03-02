"""Direction classes for forward and backward data flow analysis.

The direction determines how the analysis traverses the CFG and
propagates abstract states between nodes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import (
        AnalysisType,
        Analysis,
        AnalysisState,
    )

from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.logger import get_logger
from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations.condition import Condition

logger = get_logger()


class Direction(ABC):
    """Abstract base class for analysis direction.

    Concrete subclasses implement forward or backward traversal
    of the control flow graph during fixpoint computation.
    """

    @property
    @abstractmethod
    def IS_FORWARD(self) -> bool:
        """Return True for forward analysis, False for backward."""

    @abstractmethod
    def apply_transfer_function(
        self,
        analysis: Analysis,
        current_state: AnalysisState,
        node: Node,
        worklist: deque[Node],
        global_state: dict[int, AnalysisState[AnalysisType]],
    ) -> None:
        """Apply transfer function and propagate state to successors.

        Args:
            analysis: The analysis providing the transfer function.
            current_state: The state at the current node.
            node: The CFG node being processed.
            worklist: Queue of nodes to process.
            global_state: Mapping from node IDs to analysis states.
        """


class Forward(Direction):
    """Forward data flow analysis direction.

    Propagates information from entry to exit, following CFG edges.
    Used for analyses like reaching definitions and interval analysis.
    """

    def __init__(self) -> None:
        """Initialize forward direction."""

    @property
    def IS_FORWARD(self) -> bool:
        """Return True indicating forward analysis."""
        return True

    def apply_transfer_function(
        self,
        analysis: Analysis,
        current_state: AnalysisState,
        node: Node,
        worklist: deque[Node],
        global_state: dict[int, AnalysisState[AnalysisType]],
    ) -> None:
        condition_op = _apply_node_operations(analysis, current_state, node)
        global_state[node.node_id].post = current_state.pre

        is_conditional = (
            node.type in (NodeType.IF, NodeType.IFLOOP)
            and condition_op is not None
            and len(node.sons) == 2
        )

        for branch_index, successor in enumerate(node.sons):
            if not successor or successor.node_id not in global_state:
                continue

            propagated = _resolve_propagated_domain(
                analysis, current_state.pre,
                is_conditional, condition_op, branch_index,
            )
            son_state = global_state[successor.node_id]
            if successor.type == NodeType.IFLOOP:
                propagated = analysis.apply_widening(
                    propagated, son_state.pre, set()
                )

            changed = son_state.pre.join(propagated)
            if changed and successor not in worklist:
                worklist.append(successor)


class Backward(Direction):
    """Backward data flow analysis direction.

    Propagates information from exit to entry, following reverse CFG
    edges. Used for analyses like liveness and very busy expressions.
    """

    @property
    def IS_FORWARD(self) -> bool:
        """Return False indicating backward analysis."""
        return False

    def apply_transfer_function(
        self,
        analysis: Analysis,
        current_state: AnalysisState,
        node: Node,
        worklist: deque[Node],
        global_state: dict[int, AnalysisState[AnalysisType]],
    ) -> None:
        """Apply transfer function for backward analysis."""
        logger.error_and_raise(
            "Backward transfer function hasn't been developed yet",
            NotImplementedError,
        )


def _apply_node_operations(
    analysis: Analysis,
    current_state: AnalysisState,
    node: Node,
) -> Condition | None:
    """Run transfer function on each IR op; return Condition if present."""
    condition_op: Condition | None = None
    for operation in node.irs_ssa or [None]:
        analysis.transfer_function(
            node=node, domain=current_state.pre, operation=operation,
        )
        if isinstance(operation, Condition):
            condition_op = operation
    return condition_op


def _resolve_propagated_domain(
    analysis: Analysis,
    pre_domain: Domain,
    is_conditional: bool,
    condition_op: Condition | None,
    branch_index: int,
) -> Domain:
    """Compute the domain to propagate to a successor node."""
    if not is_conditional:
        return pre_domain
    branch_taken = branch_index == 0
    return analysis.apply_condition(pre_domain, condition_op, branch_taken)
