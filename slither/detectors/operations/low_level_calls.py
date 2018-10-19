"""
Module detecting usage of low level calls
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall


class LowLevelCalls(AbstractDetector):
    """
    Detect usage of low level calls
    """

    ARGUMENT = 'low-level-calls'
    HELP = 'low level calls'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def _contains_low_level_calls(node):
        """
             Check if the node contains Low Level Calls
        Returns:
            (bool)
        """
        return any(isinstance(ir, LowLevelCall) for ir in node.irs)

    def detect_low_level_calls(self, contract):
        ret = []
        for f in contract.functions:
            nodes = f.nodes
            assembly_nodes = [n for n in nodes if
                              self._contains_low_level_calls(n)]
            if assembly_nodes:
                ret.append((f, assembly_nodes))
        return ret

    def detect(self):
        """ Detect the functions that use low level calls
        """
        results = []
        for c in self.contracts:
            values = self.detect_low_level_calls(c)
            for func, nodes in values:
                func_name = func.name
                info = "Low level call in %s, Contract: %s, Function: %s" % (self.filename,
                                                                             c.name,
                                                                             func_name)
                self.log(info)

                sourceMapping = [n.source_mapping for n in nodes]

                results.append({'vuln': 'Low level call',
                                'sourceMapping': sourceMapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'function_name': func_name})

        return results
