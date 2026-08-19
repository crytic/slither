"""Data flow analysis engine using worklist algorithm.

Implements the generic fixpoint computation framework for
both forward and backward data flow analyses.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Generic

from slither.analyses.data_flow.engine.analysis import (
    AnalysisType,
    Analysis,
    AnalysisState,
)
from slither.analyses.data_flow.engine.domain import Domain
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function

logger = logging.getLogger("DataFlow")

_MAX_ITERATIONS = 10000
_PROGRESS_INTERVAL_SECONDS = 5.0


class Engine(Generic[AnalysisType]):
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
        self.state: dict[int, AnalysisState[AnalysisType]] = {}
        self.nodes: list[Node] = []
        self.analysis: Analysis
        self.function: Function

        self.iteration_count = 0
        self.node_visit_count: dict[int, int] = defaultdict(int)
        self.start_time: float = 0.0
        self.last_progress_time: float = 0.0

    @classmethod
    def new(
        cls,
        analysis: Analysis,
        function: Function,
        entry_domain: Domain | None = None,
    ) -> Engine[AnalysisType]:
        """Create a new engine for analyzing a function.

        Args:
            analysis: The analysis to run.
            function: The function to analyze.
            entry_domain: Optional state to seed the entry point's
                pre-state with (e.g. caller argument bindings). Joined
                into a fresh bottom value, so the engine never takes
                ownership of the caller's object. Analyses must apply
                their entry-state defaults set-if-absent so seeded
                values survive initialization.

        Returns:
            An initialized engine ready to run analysis.
        """
        engine = cls()
        engine.analysis = analysis
        engine.function = function
        analysis.prepare_for_function(function)

        for node in function.nodes:
            engine.nodes.append(node)
            engine.state[node.node_id] = AnalysisState(
                pre=analysis.bottom_value(),
                post=analysis.bottom_value(),
            )

        entry_point = function.entry_point
        if entry_domain is not None and entry_point is not None:
            engine.state[entry_point.node_id].pre.join(entry_domain)

        return engine

    def run_analysis(self) -> None:
        """Run the worklist algorithm until fixpoint is reached."""
        worklist = self._initialize_worklist()

        while worklist:
            self.iteration_count += 1
            if self._exceeded_iteration_limit(len(worklist)):
                break
            self._log_progress(len(worklist))

            node = worklist.popleft()
            self._track_node_visit(node)

            self.analysis.direction().apply_transfer_function(
                analysis=self.analysis,
                current_state=self.state[node.node_id],
                node=node,
                worklist=worklist,
                global_state=self.state,
            )

        self._log_completion()

    def result(self) -> dict[Node, AnalysisState[AnalysisType]]:
        """Return analysis results mapped by CFG node.

        Returns:
            Dict mapping each node to its final pre/post analysis state.
        """
        return {node: self.state[node.node_id] for node in self.nodes}

    def _initialize_worklist(self) -> deque[Node]:
        """Set up timing and create initial worklist."""
        self.start_time = time.time()
        self.last_progress_time = self.start_time
        self.iteration_count = 0
        self.node_visit_count.clear()

        worklist: deque[Node] = deque()
        if not self.analysis.direction().IS_FORWARD:
            message = "Backward analysis is not implemented"
            logger.error(message)
            raise NotImplementedError(message)

        entry_point = self.function.entry_point
        if entry_point is not None:
            worklist.append(entry_point)
            logger.info("Starting analysis of %s", self.function.name)
        else:
            logger.warning("No entry point for %s, skipping analysis", self.function.name)
        return worklist

    def _exceeded_iteration_limit(self, worklist_size: int) -> bool:
        """Check if iteration count exceeds safety limit."""
        if self.iteration_count <= _MAX_ITERATIONS:
            return False
        logger.error("Exceeded %d iterations! Worklist size: %d", _MAX_ITERATIONS, worklist_size)
        top_nodes = sorted(
            self.node_visit_count.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:10]
        for node_id, count in top_nodes:
            logger.error("Node %s: %d visits", node_id, count)
        return True

    def _log_progress(self, worklist_size: int) -> None:
        """Log progress at regular intervals."""
        current_time = time.time()
        if current_time - self.last_progress_time <= _PROGRESS_INTERVAL_SECONDS:
            return
        elapsed = current_time - self.start_time
        logger.info(
            "Progress: %d iterations, worklist=%d, %.1fs elapsed",
            self.iteration_count,
            worklist_size,
            elapsed,
        )
        self.last_progress_time = current_time

    def _track_node_visit(self, node: Node) -> None:
        """Track node visits and warn on excessive revisits."""
        self.node_visit_count[node.node_id] += 1
        visit_count = self.node_visit_count[node.node_id]
        if visit_count == 50:
            logger.warning("Node %s visited 50 times!", node.node_id)
        if visit_count == 100:
            logger.error("Node %s visited 100 times!", node.node_id)

    def _log_completion(self) -> None:
        """Log final analysis statistics."""
        total_time = time.time() - self.start_time
        logger.info(
            "Analysis of %s complete: %d iterations in %.2fs",
            self.function.name,
            self.iteration_count,
            total_time,
        )
