from collections import deque
from typing import Deque, Dict, Generic, List

from slither.analyses.data_flow.analysis import Analysis, AnalysisState, A
from slither.core.cfg.node import Node
from slither.core.declarations import Contract
from slither.core.declarations.function import Function

class Engine(Generic[A]):
    def __init__(self):
        self.state: Dict[int, AnalysisState[A]] = {}
        self.nodes: List[Node] = []
        self.node_to_index: Dict[Node, int] = {}
        self.analysis: Analysis = None

    @classmethod
    def new(cls, analysis: Analysis, functions: List[Function]):
        engine = cls()
        engine.analysis = analysis
        engine.functions = functions

        #  create state mapping
        node_index = 0
        for function in functions:
            for node in function.nodes:
                engine.nodes.append(node)
                engine.node_to_index[node] = node_index
                engine.state[node_index] = AnalysisState(
                    pre=analysis.bottom_value(), post=analysis.bottom_value()
                )
                node_index += 1

        return engine

    def run_analysis(self, contracts: List[Contract]):
        worklist: Deque[Node] = deque()

        if self.analysis.direction().IS_FORWARD:
            worklist.extend(self.nodes)
        else:
            raise NotImplementedError("Backward analysis is not implemented")

        while worklist:
            node = worklist.popleft()
                
            node_index = self.node_to_index[node]

            current_state = AnalysisState(
                pre=self.state[node_index].pre, post=self.state[node_index].post
            )

            self.analysis.direction().apply_transfer_function(
                analysis=self.analysis,
                current_state=current_state,
                node=node,
                worklist=worklist,
                global_state=self.state,
                functions=self.functions,
            )

    def result(self) -> Dict[Node, AnalysisState[A]]:
        result = {}
        for node, index in self.node_to_index.items():
            result[node] = self.state[index]
        return result
