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
    HELP = 'Functions allowing anyone to destruct the contract'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#suicidal'

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

                txt = "{}.{} ({}) allows anyone to destruct the contract\n"
                info = txt.format(func.contract.name,
                                  func.name,
                                  func.source_mapping_str)

                self.log(info)

                results.append({'check':self.ARGUMENT,
                                'function':{'name': func.name, 'source_mapping': func.source_mapping}})

        return results
