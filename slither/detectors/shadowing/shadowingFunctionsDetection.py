"""
    Module detecting shadowing of functions
    It is more useful as summary printer than as vuln detection
"""

from slither.detectors.abstractDetector import AbstractDetector
from slither.detectors.detectorClassification import DetectorClassification

class ShadowingFunctionsDetection(AbstractDetector):
    """
    Functions shadowing detection
    """

    vuln_name = "ShadowingFunctionContract"

    ARGUMENT = 'shadowing-function'
    HELP = 'Function Shadowing'
    CLASSIFICATION = DetectorClassification.LOW

    HIDDEN_DETECTOR = True

    def detect_shadowing(self, contract):
        functions_declared = set([x.full_name for x in contract.functions])
        ret = {}
        for father in contract.inheritances:
            functions_declared_father = ([x.full_name for x in father.functions])
            inter = functions_declared.intersection(functions_declared_father)
            if inter:
                ret[father] = inter
        return ret

    def detect(self):
        """ detect shadowing

        recursively visit the calls
        returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """
        results = []
        for c in self.contracts:
            shadowing = self.detect_shadowing(c)
            if shadowing:
                for contract, funcs in shadowing.iteritems():
                    results.append({'vuln':self.vuln_name,
                                    'filename': self.filename,
                                    'contractShadower': c.name,
                                    'contract': contract.name,
                                    'funcs': list(funcs)})

        return results
