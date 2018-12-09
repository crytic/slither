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

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#low-level-calls'

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
        all_info = ''
        for c in self.contracts:
            values = self.detect_low_level_calls(c)
            for func, nodes in values:
                info = "Low level call in {}.{} ({}):\n"
                info = info.format(func.contract.name, func.name, func.source_mapping_str)
                for node in nodes:
                    info += "\t-{} {}\n".format(str(node.expression), node.source_mapping_str)
                all_info += info

                json = self.generate_json_result(info)
                self.add_function_to_json(func, json)
                self.add_nodes_to_json(nodes, json)
                results.append(json)



        if all_info != '':
            self.log(all_info)
        return results
