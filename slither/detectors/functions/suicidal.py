"""
Module detecting suicidal contract

A suicidal contract is an unprotected function that calls selfdestruct
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

class Suicidal(AbstractDetector):
    """
    Unprotected function detector
    """

    ARGUMENT = 'suicidal'
    HELP = 'Suicidal functions'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def detect_suicidal_func(func):
        """ Detect if the function is suicidal

        Detect the public functions calling suicide/selfdestruct without protection
        Returns:
            (bool): True if the function is suicidal
        """

        if func.is_constructor:
            return False

        if func.visibility != 'public':
            return False

        calls = [c.name for c in func.internal_calls]
        if not ('suicide(address)' in calls or 'selfdestruct(address)' in calls):
            return False

        if func.is_protected():
            return False

        return True

    def detect_suicidal(self, contract):
        ret = []
        for f in [f for f in contract.functions if f.contract == contract]:
            if self.detect_suicidal_func(f):
                ret.append(f)
        return ret

    def detect(self):
        """ Detect the suicidal functions
        """
        results = []
        for c in self.contracts:
            functions = self.detect_suicidal(c)
            for func in functions:
                func_name = func.name

                txt = "Suicidal function in {} Contract: {}, Function: {}"
                info = txt.format(self.filename,
                                  c.name,
                                  func_name)

                self.log(info)

                results.append({'vuln': 'SuicidalFunc',
                                'sourceMapping': func.source_mapping,
                                'filename': self.filename,
                                'contract': c.name,
                                'func': func_name})

        return results
