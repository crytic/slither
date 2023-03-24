"""
Module detecting usage of inline assembly
"""
from typing import List, Tuple

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.contract import Contract
from slither.core.declarations.function_contract import FunctionContract
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class Assembly(AbstractDetector):
    """
    Detect usage of inline assembly
    """

    ARGUMENT = "assembly"
    HELP = "Assembly usage"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#assembly-usage"

    WIKI_TITLE = "Assembly usage"
    WIKI_DESCRIPTION = "The use of assembly is error-prone and should be avoided."
    WIKI_RECOMMENDATION = "Do not use `evm` assembly."

    @staticmethod
    def _contains_inline_assembly_use(node: Node) -> bool:
        """
             Check if the node contains ASSEMBLY type
        Returns:
            (bool)
        """
        return node.type == NodeType.ASSEMBLY

    def detect_assembly(self, contract: Contract) -> List[Tuple[FunctionContract, List[Node]]]:
        ret = []
        for f in contract.functions:
            if f.contract_declarer != contract:
                continue
            nodes = f.nodes
            assembly_nodes = [n for n in nodes if self._contains_inline_assembly_use(n)]
            if assembly_nodes:
                ret.append((f, assembly_nodes))
        return ret

    def _detect(self) -> List[Output]:
        """Detect the functions that use inline assembly"""
        results = []
        for c in self.contracts:
            values = self.detect_assembly(c)
            for func, nodes in values:
                info: DETECTOR_INFO = [func, " uses assembly\n"]

                # sort the nodes to get deterministic results
                nodes.sort(key=lambda x: x.node_id)

                for node in nodes:
                    info += ["\t- ", node, "\n"]

                res = self.generate_result(info)
                results.append(res)

        return results
