from collections import deque
from typing import Deque, Dict, Generic, List

from slither.analyses.data_flow.analysis import A, Analysis, AnalysisState
from slither.core.cfg.node import Node
from slither.core.declarations import Contract
from slither.core.declarations.function import Function


class Engine(Generic[A]):
    def __init__(self):
        self.state: Dict[int, AnalysisState[A]] = {}
        self.nodes: List[Node] = []
        self.analysis: Analysis = None

    @classmethod
    def new(cls, analysis: Analysis, functions: List[Function]):
        engine = cls()
        engine.analysis = analysis
        engine.functions = functions

        for function in functions:
            nodes = function.nodes
            for node, indx in enumerate(nodes):
                engine.state[indx] = AnalysisState(
                    pre=analysis.bottom_value(), post=analysis.bottom_value()
                )

        return engine

    def run_analysis(self, contracts: List[Contract]):
        worklist: Deque[Node] = deque()

        # get all nodes from all contracts
        all_nodes = []
        for contract in contracts:
            for function in contract.functions:
                all_nodes.extend(function.nodes)

        if self.analysis.direction().IS_FORWARD:
            worklist.extend(all_nodes)
        else:
            raise NotImplementedError("Backward analysis is not implemented")

        while worklist:
            node = worklist.popleft()
            node_index = self.nodes.index(node)

            # Clone current state
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
        return self.state
