from collections import deque
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

        if self.analysis.direction().IS_FORWARD:
            worklist.extend(self.nodes)
        else:
            raise NotImplementedError("Backward analysis is not implemented")

        while worklist:
            node = worklist.popleft()

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

    def result(self) -> Dict[Node, AnalysisState[A]]:
        result = {}
        for node in self.nodes:
            result[node] = self.state[node.node_id]
        return result
