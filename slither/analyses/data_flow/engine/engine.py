"""Data flow analysis engine using worklist algorithm.

Implements the generic fixpoint computation framework for
both forward and backward data flow analyses.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Generic, List, Set

from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState
from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function

logger = get_logger()


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
        self.state: Dict[int, AnalysisState[A]] = {}
        self.nodes: List[Node] = []
        self.analysis: Analysis
        self.function: Function

        # Performance instrumentation
        self.iteration_count = 0
        self.node_visit_count: Dict[int, int] = defaultdict(int)
        self.start_time: float = 0.0
        self.last_progress_time: float = 0.0

    @classmethod
    def new(cls, analysis: Analysis, function: Function) -> "Engine[A]":
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
        state_vars: Set[str] = set()
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
        """Count loops by detecting back edges in the CFG."""
        if not function.nodes:
            return 0

        visited: Set[int] = set()
        in_stack: Set[int] = set()
        back_edges = 0

        def dfs(node: Node) -> None:
            nonlocal back_edges
            visited.add(node.node_id)
            in_stack.add(node.node_id)

            for successor in node.sons:
                if successor.node_id not in visited:
                    dfs(successor)
                elif successor.node_id in in_stack:
                    # Back edge found - indicates a loop
                    back_edges += 1

            in_stack.remove(node.node_id)

        entry = function.entry_point
        if entry is not None:
            dfs(entry)

        return back_edges

    def run_analysis(self) -> None:
        """Run the worklist algorithm until fixpoint is reached."""
        worklist: Deque[Node] = deque()

        # Instrumentation constants
        MAX_ITERATIONS = 10000
        PROGRESS_INTERVAL = 5.0  # seconds

        # Initialize timing
        self.start_time = time.time()
        self.last_progress_time = self.start_time
        self.iteration_count = 0
        self.node_visit_count.clear()

        if self.analysis.direction().IS_FORWARD:
            entry_point = self.function.entry_point
            if entry_point is not None:
                worklist.append(entry_point)
                logger.info("Starting analysis of {name}", name=self.function.name)
        else:
            raise NotImplementedError("Backward analysis is not implemented")

        # Get telemetry instance
        telemetry = get_telemetry()

        while worklist:
            # Track iteration count
            self.iteration_count += 1

            # Record telemetry
            if telemetry is not None and telemetry.enabled:
                telemetry.record_worklist_iteration()

            # Safety limit check
            if self.iteration_count > MAX_ITERATIONS:
                logger.error(
                    "Exceeded {max} iterations! Worklist size: {size}",
                    max=MAX_ITERATIONS,
                    size=len(worklist),
                )
                top_nodes = sorted(
                    self.node_visit_count.items(), key=lambda x: x[1], reverse=True
                )[:10]
                for node_id, count in top_nodes:
                    logger.error("Node {node_id}: {count} visits", node_id=node_id, count=count)
                break

            # Progress logging every PROGRESS_INTERVAL seconds
            current_time = time.time()
            if current_time - self.last_progress_time > PROGRESS_INTERVAL:
                elapsed = current_time - self.start_time
                logger.info(
                    "Progress: {iterations} iterations, worklist={size}, {elapsed:.1f}s elapsed",
                    iterations=self.iteration_count,
                    size=len(worklist),
                    elapsed=elapsed,
                )
                self.last_progress_time = current_time

            node = worklist.popleft()

            # Track node visits
            self.node_visit_count[node.node_id] += 1
            if self.node_visit_count[node.node_id] == 50:
                logger.warning("Node {node_id} visited 50 times!", node_id=node.node_id)
            if self.node_visit_count[node.node_id] == 100:
                logger.error("Node {node_id} visited 100 times!", node_id=node.node_id)

            current_state = AnalysisState(
                pre=self.state[node.node_id].pre, post=self.state[node.node_id].post
            )

            self.analysis.direction().apply_transfer_function(
                analysis=self.analysis,
                current_state=current_state,
                node=node,
                worklist=worklist,
                global_state=self.state,
            )

        # Final statistics
        total_time = time.time() - self.start_time
        logger.info(
            "Analysis of {name} complete: {iterations} iterations in {time:.2f}s",
            name=self.function.name,
            iterations=self.iteration_count,
            time=total_time,
        )

        # Record fixpoint reached
        if telemetry is not None and telemetry.enabled:
            telemetry.record_fixpoint_reached()

    def result(self) -> Dict[Node, AnalysisState[A]]:
        """Return analysis results mapped by CFG node.

        Returns:
            Dict mapping each node to its final pre/post analysis state.
        """
        result = {}
        for node in self.nodes:
            result[node] = self.state[node.node_id]
        return result
