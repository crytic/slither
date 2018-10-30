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
    HELP = 'Low level calls'
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
        for f in [f for f in contract.functions if contract == f.contract]:
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
                info = "Low level call in {}.{} ({})"
                info = info.format(func.contract.name, func.name, func.source_mapping_str)
                self.log(info)

                sourceMapping = [n.source_mapping for n in nodes]

                results.append({'vuln': 'Low level call',
                                'sourceMapping': sourceMapping,
                                'filename': self.filename,
                                'contract': func.contract.name,
                                'function_name': func.name})

        return results
