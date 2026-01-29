import time
from collections import defaultdict, deque
from typing import Deque, Dict, Generic, List

from slither.analyses.data_flow.engine.analysis import A, Analysis, AnalysisState
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function


class Engine(Generic[A]):
    def __init__(self):
        self.state: Dict[int, AnalysisState[A]] = {}
        self.nodes: List[Node] = []
        self.analysis: Analysis
        self.function: Function  # Single function being analyzed

        # Performance instrumentation
        self.iteration_count = 0
        self.node_visit_count: Dict[int, int] = defaultdict(int)
        self.start_time: float = 0.0
        self.last_progress_time: float = 0.0

    @classmethod
    def new(cls, analysis: Analysis, function: Function):
        engine = cls()
        engine.analysis = analysis
        engine.function = function  # Store single function

        # Create state mapping for nodes in this single function only
        # Data flow analysis operates on one function's CFG at a time
        for node in function.nodes:
            engine.nodes.append(node)
            engine.state[node.node_id] = AnalysisState(
                pre=analysis.bottom_value(), post=analysis.bottom_value()
            )

        return engine

    def run_analysis(self):
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
                print(f"[ENGINE] Starting analysis of {self.function.name}")
        else:
            raise NotImplementedError("Backward analysis is not implemented")

        while worklist:
            # Track iteration count
            self.iteration_count += 1

            # Safety limit check
            if self.iteration_count > MAX_ITERATIONS:
                print(f"\n[ENGINE] ERROR: Exceeded {MAX_ITERATIONS} iterations!")
                print(f"[ENGINE] Worklist size: {len(worklist)}")
                print(f"[ENGINE] Top 10 most visited nodes:")
                for node_id, count in sorted(
                    self.node_visit_count.items(), key=lambda x: x[1], reverse=True
                )[:10]:
                    print(f"  Node {node_id}: {count} visits")
                break

            # Progress logging every PROGRESS_INTERVAL seconds
            current_time = time.time()
            if current_time - self.last_progress_time > PROGRESS_INTERVAL:
                elapsed = current_time - self.start_time
                print(
                    f"[ENGINE] Progress: {self.iteration_count} iterations, "
                    f"worklist={len(worklist)}, {elapsed:.1f}s elapsed"
                )
                self.last_progress_time = current_time

            node = worklist.popleft()

            # Track node visits
            self.node_visit_count[node.node_id] += 1
            if self.node_visit_count[node.node_id] == 50:
                print(f"[ENGINE] WARNING: Node {node.node_id} visited 50 times!")
            if self.node_visit_count[node.node_id] == 100:
                print(f"[ENGINE] CRITICAL: Node {node.node_id} visited 100 times!")

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
        print(
            f"[ENGINE] Analysis of {self.function.name} complete: "
            f"{self.iteration_count} iterations in {total_time:.2f}s"
        )

    def result(self) -> Dict[Node, AnalysisState[A]]:
        result = {}
        for node in self.nodes:
            result[node] = self.state[node.node_id]
        return result
