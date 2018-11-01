"""
    Module detecting shadowing of functions
    It is more useful as summary printer than as vuln detection
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ShadowingFunctionsDetection(AbstractDetector):
    """
    Functions shadowing detection
    """

    vuln_name = "ShadowingFunctionContract"

    ARGUMENT = 'shadowing-function'
    HELP = 'Function Shadowing'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    def detect_shadowing(self, contract):
        functions_declared = set([x.full_name for x in contract.functions])
        ret = {}
        for father in contract.inheritance:
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
        for c in sorted(self.contracts, key=lambda c: c.name):
            shadowing = self.detect_shadowing(c)
            if shadowing:
                for contract, funcs in sorted(shadowing.items(), key=lambda x: (x[0].name, str(list(x[1])))):
                    results.append({'vuln': self.vuln_name,
                                    'filename': self.filename,
                                    'contractShadower': c.name,
                                    'contract': contract.name,
                                    'funcs': list(funcs)})

        return results
