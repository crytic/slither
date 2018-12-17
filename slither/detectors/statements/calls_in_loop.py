"""
"""
from slither.core.cfg.node import NodeType
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, LibraryCall,
                                        LowLevelCall, Send, Transfer)


class MultipleCallsInLoop(AbstractDetector):
    """
    """

    ARGUMENT = 'calls-loop'
    HELP = 'Multiple calls in a loop'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description/_edit#calls-inside-a-loop'

    @staticmethod
    def call_in_loop(node, in_loop, visited, ret):
        if node in visited:
            return
        # shared visited
        visited.append(node)

        if node.type == NodeType.STARTLOOP:
            in_loop = True
        elif node.type == NodeType.ENDLOOP:
            in_loop = False

        if in_loop:
            for ir in node.irs:
                if isinstance(ir, (LowLevelCall,
                                   HighLevelCall,
                                   Send,
                                   Transfer)):
                    if isinstance(ir, LibraryCall):
                        continue
                    ret.append(node)

        for son in node.sons:
            MultipleCallsInLoop.call_in_loop(son, in_loop, visited, ret)

    @staticmethod
    def detect_call_in_loop(contract):
        ret = []
        for f in contract.functions + contract.modifiers:
            if f.contract == contract and f.is_implemented:
                MultipleCallsInLoop.call_in_loop(f.entry_point,
                                                 False, [], ret)

        return ret

    def detect(self):
        """
        """
        results = []
        for c in self.contracts:
            values = self.detect_call_in_loop(c)
            for node in values:
                func = node.function
                info = "{}.{} has external calls inside a loop:\n"
                info = info.format(func.contract.name, func.name)

                info += "\t- {} ({})\n".format(node.expression, node.source_mapping_str)

                self.log(info)

                json = self.generate_json_result(info)
                self.add_function_to_json(func, json)
                self.add_nodes_to_json([node], json)
                results.append(json)

        return results
