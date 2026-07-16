"""Direction classes for forward and backward data flow analysis.

The direction determines how the analysis traverses the CFG and
propagates abstract states between nodes.
"""

from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING

from slither.analyses.data_flow.engine.domain import Domain

if TYPE_CHECKING:
    from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState
    from slither.core.declarations.function import Function

from slither.analyses.data_flow.engine.loop import (
    ControlFlowEdgeId,
    LoopHeaderFixpoint,
    LoopStructure,
)
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry
from slither.core.cfg.node import Node, NodeType
from slither.slithir.operations.condition import Condition


class Direction(ABC):
    """Abstract base class for analysis direction.

    Concrete subclasses implement forward or backward traversal
    of the control flow graph during fixpoint computation.
    """

    @property
    @abstractmethod
    def IS_FORWARD(self) -> bool:
        """Return True for forward analysis, False for backward."""

    def prepare_for_function(self, function: "Function") -> None:
        """Reset function-specific traversal metadata."""
        return None

    @abstractmethod
    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: deque[Node],
        global_state: dict[int, "AnalysisState[A]"],
    ) -> None:
        """Apply transfer function and propagate state to successors/predecessors.

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
        self._loops = LoopStructure()
        self._loop_fixpoints: dict[int, LoopHeaderFixpoint] = {}

    def prepare_for_function(self, function: "Function") -> None:
        """Classify natural loops before worklist traversal starts."""
        self._loops = LoopStructure.from_function(function)
        self._loop_fixpoints = {}
        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_loop_headers(len(self._loops.loops))

    @property
    def loop_structure(self) -> LoopStructure:
        """Return deterministic loop metadata for the active function."""
        return self._loops

    @property
    def loop_fixpoints(self) -> tuple[LoopHeaderFixpoint, ...]:
        """Return loop trackers ordered by header node ID."""
        return tuple(self._loop_fixpoints[node_id] for node_id in sorted(self._loop_fixpoints))

    @property
    def IS_FORWARD(self) -> bool:
        """Return True indicating forward analysis."""
        return True

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: deque[Node],
        global_state: dict[int, "AnalysisState[A]"],
    ) -> None:
        """Transfer one node and propagate each complete outgoing state."""
        input_domain = current_state.pre
        output_domain = input_domain.deep_copy()
        condition_op: Condition | None = None
        for operation in node.irs_ssa or [None]:
            analysis.transfer_function(node=node, domain=output_domain, operation=operation)
            if isinstance(operation, Condition):
                condition_op = operation

        global_state[node.node_id].post = output_domain
        self._record_loop_output(node, output_domain)

        is_conditional = (
            node.type in (NodeType.IF, NodeType.IFLOOP)
            and condition_op is not None
            and len(node.sons) == 2
        )
        for i, successor in enumerate(node.sons):
            if not successor or successor.node_id not in global_state:
                continue
            outgoing = output_domain
            if is_conditional and condition_op is not None:
                outgoing = analysis.apply_condition(output_domain, condition_op, i == 0)
            changed = self._propagate_edge(
                analysis,
                node,
                successor,
                outgoing,
                global_state[successor.node_id],
            )
            self._schedule(successor, changed, worklist)

    def _record_loop_output(self, node: Node, output: "Domain") -> None:
        tracker = self._loop_fixpoints.get(node.node_id)
        if tracker is not None:
            tracker.record_output(output)

    def _propagate_edge(
        self,
        analysis: "Analysis",
        source: Node,
        destination: Node,
        outgoing: "Domain",
        destination_state: "AnalysisState",
    ) -> bool:
        loop = self._loops.header(destination.node_id)
        if loop is None:
            return destination_state.pre.join(outgoing)
        tracker = self._loop_fixpoints.setdefault(
            destination.node_id,
            LoopHeaderFixpoint(loop.header_id, analysis.loop_variables(loop.header_id)),
        )
        edge = ControlFlowEdgeId(source.node_id, destination.node_id)
        is_back_edge = self._loops.is_back_edge(edge)
        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled and is_back_edge:
            telemetry.record_back_edge()
        generation_before = tracker.generation
        facts_before = tracker.generation_fact_ids
        update = tracker.update(edge, outgoing, is_back_edge, analysis)
        if telemetry is not None and telemetry.enabled:
            telemetry.record_loop_update(
                header_key=repr(tracker.header_id),
                is_back_edge=is_back_edge,
                changed=update.changed,
                generation_advanced=tracker.generation > generation_before,
                facts_replaced=tracker.generation_fact_ids != facts_before,
                live_generation_facts=len(tracker.generation_fact_ids),
            )
        if update.changed and update.state is not None:
            destination_state.pre = update.state
        return update.changed

    @staticmethod
    def _schedule(successor: Node, changed: bool, worklist: deque[Node]) -> None:
        telemetry = get_telemetry()
        if changed and successor not in worklist:
            worklist.append(successor)
            if telemetry is not None and telemetry.enabled:
                telemetry.record_worklist_enqueue(len(worklist))
        elif not changed and telemetry is not None and telemetry.enabled:
            telemetry.record_transfer_rerun_prevented()


class Backward(Direction):
    """Backward data flow analysis direction.

    Propagates information from exit to entry, following reverse CFG edges.
    Used for analyses like liveness and very busy expressions.
    """

    @property
    def IS_FORWARD(self) -> bool:
        """Return False indicating backward analysis."""
        return False

    def apply_transfer_function(
        self,
        analysis: "Analysis",
        current_state: "AnalysisState",
        node: Node,
        worklist: deque[Node],
        global_state: dict[int, "AnalysisState[A]"],
    ) -> None:
        """Apply transfer function for backward analysis (not yet implemented)."""
        raise NotImplementedError("Backward transfer function hasn't been developed yet")
