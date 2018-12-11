"""
Module detecting unused return values from external calls
"""

from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.core.variables.state_variable import StateVariable

class UnusedReturnValues(AbstractDetector):
    """
    If the return value of a function is never used, it's likely to be bug
    """

    ARGUMENT = 'unused-return'
    HELP = 'Unused return values'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#unused-return'

    def detect_unused_return_values(self, f):
        """
            Return the nodes where the return value of a call is unused
        Args:
            f (Function)
        Returns:
            list(Node)
        """
        values_returned = []
        nodes_origin = {}
        for n in f.nodes:
            for ir in n.irs:
                if isinstance(ir, HighLevelCall):
                    # if a return value is stored in a state variable, it's ok
                    if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                        values_returned.append(ir.lvalue)
                        nodes_origin[ir.lvalue] = ir
                for read in ir.read:
                    if read in values_returned:
                        values_returned.remove(read)

        return [nodes_origin[value].node for value in values_returned]

    def detect(self):
        """ Detect unused high level calls that return a value but are never used
        """
        results = []
        for c in self.slither.contracts:
            for f in c.functions + c.modifiers:
                if f.contract != c:
                    continue
                unused_return = self.detect_unused_return_values(f)
                if unused_return:
                    info = "{}.{} ({}) does not use the value returned by external calls:\n"
                    info = info.format(f.contract.name,
                                       f.name,
                                       f.source_mapping_str)
                    for node in unused_return:
                        info += "\t-{} ({})\n".format(node.expression, node.source_mapping_str)
                    self.log(info)

                    json = self.generate_json_result(info)
                    self.add_function_to_json(f, json)
                    self.add_nodes_to_json(unused_return, json)
                    results.append(json)

        return results
