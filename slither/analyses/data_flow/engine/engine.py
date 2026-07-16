"""Data flow analysis engine using worklist algorithm.

Implements the generic fixpoint computation framework for
both forward and backward data flow analyses.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import TYPE_CHECKING, Generic

from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState
from slither.analyses.data_flow.engine.loop import LoopStructure
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.telemetry import SolverTelemetry


logger = get_logger()
MAX_ANALYSIS_ITERATIONS = 10_000
PROGRESS_INTERVAL_SECONDS = 5.0


class Engine(Generic[A]):
    """Worklist-based data flow analysis engine.

    Computes fixpoints for data flow analyses over function CFGs.
    Tracks iteration counts and node visits for performance profiling.

    Attributes:
        state: Mapping from node IDs to pre/post analysis states.
        nodes: List of CFG nodes in the analyzed function.
        analysis: The analysis instance providing transfer functions.
        function: The function being analyzed.
        iteration_count: Total worklist iterations performed.
        node_visit_count: Visit count per node for cycle detection.
    """

    def __init__(self) -> None:
        """Initialize an empty engine instance."""
        self.state: dict[int, AnalysisState[A]] = {}
        self.nodes: list[Node] = []
        self.analysis: Analysis
        self.function: Function

        # Performance instrumentation
        self.iteration_count = 0
        self.node_visit_count: dict[int, int] = defaultdict(int)
        self.start_time: float = 0.0
        self.last_progress_time: float = 0.0

    @classmethod
    def new(cls, analysis: Analysis, function: Function) -> Engine[A]:
        """Create a new engine for analyzing a function.

        Args:
            analysis: The analysis to run.
            function: The function to analyze.

        Returns:
            An initialized engine ready to run analysis.
        """
        engine = cls()
        engine.analysis = analysis
        engine.function = function

        # Allow analysis to prepare for this function (e.g., collect thresholds)
        analysis.prepare_for_function(function)
        analysis.direction().prepare_for_function(function)

        # Create state mapping for nodes in this single function only
        for node in function.nodes:
            engine.nodes.append(node)
            engine.state[node.node_id] = AnalysisState(
                pre=analysis.bottom_value(), post=analysis.bottom_value()
            )

        # Record function metrics for telemetry
        engine._record_function_metrics(function)

        return engine

    def _record_function_metrics(self, function: Function) -> None:
        """Record function-level metrics for telemetry."""
        telemetry = get_telemetry()
        if telemetry is None or not telemetry.enabled:
            return

        # Count loops by detecting back edges
        loop_count = self._count_loops(function)

        # Count external calls
        external_call_count = 0
        for node in function.nodes:
            if hasattr(node, "external_calls_as_expressions"):
                external_call_count += len(node.external_calls_as_expressions)

        # Count state variables accessed
        state_vars: set[str] = set()
        for node in function.nodes:
            if hasattr(node, "state_variables_read"):
                state_vars.update(str(var) for var in node.state_variables_read)
            if hasattr(node, "state_variables_written"):
                state_vars.update(str(var) for var in node.state_variables_written)

        telemetry.record_function_info(
            name=function.name,
            cfg_nodes=len(function.nodes),
            basic_blocks=len(function.nodes),  # In Slither, nodes are basic blocks
            parameters=len(function.parameters),
            local_variables=len(function.local_variables),
            state_variables_accessed=len(state_vars),
            loops=loop_count,
            external_calls=external_call_count,
        )

    def _count_loops(self, function: Function) -> int:
        """Count stable dominator-classified natural-loop headers."""
        return len(LoopStructure.from_function(function).loops)

    def run_analysis(self) -> None:
        """Run the worklist algorithm until fixpoint is reached."""
        self.start_time = time.time()
        self.last_progress_time = self.start_time
        self.iteration_count = 0
        self.node_visit_count.clear()
        telemetry = get_telemetry()
        worklist = self._initialize_worklist(telemetry)

        while worklist and self._run_iteration(worklist, telemetry):
            pass

        total_time = time.time() - self.start_time
        logger.info(
            "Analysis of {name} complete: {iterations} iterations in {time:.2f}s",
            name=self.function.name,
            iterations=self.iteration_count,
            time=total_time,
        )
        if telemetry is not None and telemetry.enabled:
            telemetry.record_fixpoint_reached()

    def _initialize_worklist(self, telemetry: SolverTelemetry | None) -> deque[Node]:
        """Create the initial FIFO queue without changing traversal semantics."""
        if not self.analysis.direction().IS_FORWARD:
            raise NotImplementedError("Backward analysis is not implemented")
        worklist: deque[Node] = deque()
        entry_point = self.function.entry_point
        if entry_point is None:
            return worklist
        worklist.append(entry_point)
        if telemetry is not None and telemetry.enabled:
            telemetry.record_worklist_enqueue(len(worklist))
        logger.info("Starting analysis of {name}", name=self.function.name)
        return worklist

    def _run_iteration(
        self,
        worklist: deque[Node],
        telemetry: SolverTelemetry | None,
    ) -> bool:
        """Run one FIFO worklist iteration and report whether to continue."""
        self.iteration_count += 1
        if telemetry is not None and telemetry.enabled:
            telemetry.record_worklist_iteration()
        if self.iteration_count > MAX_ANALYSIS_ITERATIONS:
            self._log_iteration_limit(worklist)
            return False
        self._log_progress_if_due(worklist)
        node = worklist.popleft()
        self._record_node_visit(node, worklist, telemetry)
        current_state = AnalysisState(
            pre=self.state[node.node_id].pre,
            post=self.state[node.node_id].post,
        )
        self.analysis.direction().apply_transfer_function(
            analysis=self.analysis,
            current_state=current_state,
            node=node,
            worklist=worklist,
            global_state=self.state,
        )
        return True

    def _log_iteration_limit(self, worklist: deque[Node]) -> None:
        logger.error(
            "Exceeded {max} iterations! Worklist size: {size}",
            max=MAX_ANALYSIS_ITERATIONS,
            size=len(worklist),
        )
        top_nodes = sorted(self.node_visit_count.items(), key=lambda item: item[1], reverse=True)[
            :10
        ]
        for node_id, count in top_nodes:
            logger.error("Node {node_id}: {count} visits", node_id=node_id, count=count)

    def _log_progress_if_due(self, worklist: deque[Node]) -> None:
        current_time = time.time()
        if current_time - self.last_progress_time <= PROGRESS_INTERVAL_SECONDS:
            return
        logger.info(
            "Progress: {iterations} iterations, worklist={size}, {elapsed:.1f}s elapsed",
            iterations=self.iteration_count,
            size=len(worklist),
            elapsed=current_time - self.start_time,
        )
        self.last_progress_time = current_time

    def _record_node_visit(
        self,
        node: Node,
        worklist: deque[Node],
        telemetry: SolverTelemetry | None,
    ) -> None:
        self.node_visit_count[node.node_id] += 1
        visit_count = self.node_visit_count[node.node_id]
        if telemetry is not None and telemetry.enabled:
            telemetry.record_worklist_pop(
                node.node_id,
                visit_count,
                len(worklist) + 1,
                self._state_local_constraint_count(self.state[node.node_id].pre),
            )
        if visit_count == 50:
            logger.warning("Node {node_id} visited 50 times!", node_id=node.node_id)
        if visit_count == 100:
            logger.error("Node {node_id} visited 100 times!", node_id=node.node_id)

    @staticmethod
    def _state_local_constraint_count(domain: object) -> int:
        """Count state-local constraints without coupling the engine to a domain."""
        state = getattr(domain, "state", None)
        getter = getattr(state, "get_path_constraints", None)
        if getter is None:
            return 0
        return len(getter())

    def result(self) -> dict[Node, AnalysisState[A]]:
        """Return analysis results mapped by CFG node.

        Returns:
            Dict mapping each node to its final pre/post analysis state.
        """
        result = {}
        for node in self.nodes:
            result[node] = self.state[node.node_id]
        return result
