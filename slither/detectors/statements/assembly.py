"""
Module detecting usage of inline assembly
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType


class Assembly(AbstractDetector):
    """
    Detect usage of inline assembly
    """

    ARGUMENT = 'assembly'
    HELP = 'Assembly usage'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#assembly-usage'


    WIKI_TITLE = 'Assembly usage'
    WIKI_DESCRIPTION = 'The use of assembly is error-prone and should be avoided.'
    WIKI_RECOMMENDATION = 'Do not use evm assembly.'

    @staticmethod
    def _contains_inline_assembly_use(node):
        """
             Check if the node contains ASSEMBLY type
        Returns:
            (bool)
        """
        return node.type == NodeType.ASSEMBLY

    def detect_assembly(self, contract):
        ret = []
        for f in contract.functions:
            if f.contract != contract:
                continue
            nodes = f.nodes
            assembly_nodes = [n for n in nodes if
                              self._contains_inline_assembly_use(n)]
            if assembly_nodes:
                ret.append((f, assembly_nodes))
        return ret

    def _detect(self):
        """ Detect the functions that use inline assembly
        """
        results = []
        for c in self.contracts:
            values = self.detect_assembly(c)
            for func, nodes in values:
                info = "{}.{} uses assembly ({})\n"
                info = info.format(func.contract.name, func.name, func.source_mapping_str)

                for node in nodes:
                    info += "\t- {}\n".format(node.source_mapping_str)

                json = self.generate_json_result(info)
                self.add_function_to_json(func, json)
                self.add_nodes_to_json(nodes, json)
                results.append(json)

        return results
