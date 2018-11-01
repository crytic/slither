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
            nodes = f.nodes
            assembly_nodes = [n for n in nodes if
                              self._contains_inline_assembly_use(n)]
            if assembly_nodes:
                ret.append((f, assembly_nodes))
        return ret

    def detect(self):
        """ Detect the functions that use inline assembly
        """
        results = []
        for c in sorted(self.contracts, key=lambda c: c.name):
            values = self.detect_assembly(c)
            for func, nodes in sorted(values, key=lambda v: v[0].name):
                func_name = func.name
                info = "Assembly in %s, Contract: %s, Function: %s" % (self.filename,
                                                                       c.name,
                                                                       func_name)
                self.log(info)

                sourceMapping = [n.source_mapping for n in nodes]

                results.append({'vuln': 'Assembly',
                                'sourceMapping': sourceMapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'function_name': func_name})

        return results
