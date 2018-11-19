"""
Module detecting unused return values from external calls
"""

from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations.high_level_call import HighLevelCall

class UnusedReturnValues(AbstractDetector):
    """
    If the return value of a function is never used, it's likely to be bug
    """

    ARGUMENT = 'unused-return'
    HELP = 'Unused return values'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    @staticmethod
    def lvalues_of_operations(contract):
        ret = []

        for f in contract.all_functions_called + contract.modifiers:
            for n in f.nodes:
                for ir in n.irs:
                    ret.append(ir)

        return ret

    @staticmethod
    def unused_lvalues_in_high_level_calls(irs):
        # Checking HighLevelCall - same process could work for LowLevelCall
        lvalues = []
        for ir in irs:
            if isinstance(ir, HighLevelCall):
                if (ir.lvalue.contract.get_functions_reading_from_variable(ir.lvalue) == []):
                    lvalues.append(ir.lvalue)

        return lvalues

    def detect_unused_return_values(self, contract):
        lvalues_of_operations = self.lvalues_of_operations(contract)
        unused_lvalues = self.unused_lvalues_in_high_level_calls(lvalues_of_operations)

        return unused_lvalues

    def detect(self):
        """ Detect unused high level calls that return a value but are never used
        """
        results = []
        for c in self.slither.contracts_derived:
            unused_return_values = self.detect_unused_return_values(c)

            if unused_return_values:
                funcs_with_unused_return_value_by_contract = defaultdict(list)

                for unused_return_value in unused_return_values:
                    funcs_with_unused_return_value_by_contract[unused_return_value.contract.name].append(unused_return_value.function.name)

                for contract, functions in funcs_with_unused_return_value_by_contract.items():
                    info = "Unused return value from external call in %s Contract: %s, Function: %s" % (self.filename, contract, ",".join(functions))
                    self.log(info)

                    sourceMapping = [v.source_mapping for v in unused_return_values]

                    results.append({'vuln': 'UnusedReturn',
                                    'sourceMapping': sourceMapping,
                                    'filename': self.filename,
                                    'contract': c.name,
                                    'unusedReturns': functions})
        return results
