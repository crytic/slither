"""
Module detecting usage of unused return value
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations.lvalue import OperationWithLValue


class UnusedReturnValues(AbstractDetector):
    """
    Detect usage of unused return value
    """

    ARGUMENT = 'unused-return-value'
    HELP = 'unused return value'
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    def total_values(self):
        all_values = []
        for c in self.contracts:
            for f in c.functions:
                for n in f.nodes:
                    for ir in n.irs:
                        if isinstance(ir, OperationWithLValue) and ir.lvalue not in all_values:
                            all_values.append(ir.lvalue)
        return all_values

    def actual_operation(self, read_list):
        send = []
        for c in self.contracts:
            for f in c.functions:
                for n in f.nodes:
                    for ir in n.irs:
                        if ir.read not in read_list:
                            send.append((f, c))
        return send

    def detect(self):
        results = []
        read_list = self.total_values()
        import ipdb;ipdb.set_trace()
        values = self.actual_operation(read_list)
        for func, contract in values:
            func_name = func.name
            info = "Unused return value in %s, Contract: %s, Function: %s" % (self.filename,
                                                                              contract.name,
                                                                              func_name)
            self.log(info)

            results.append({'vuln': 'Unused return value',
                            'filename': self.filename,
                            'contract': contract.name,
                            'function_name': func_name})
        return results
