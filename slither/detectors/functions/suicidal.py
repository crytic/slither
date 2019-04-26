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

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#suicidal'


    WIKI_TITLE = 'Suicidal'
    WIKI_DESCRIPTION = 'Unprotected call to a function executing `selfdestruct`/`suicide`.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Suicidal{
    function kill() public{
        selfdestruct(msg.sender);
    }
}
```
Bob calls `kill` and destructs the contract.'''

    WIKI_RECOMMENDATION = 'Protect access to all sensitive functions.'

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
        for f in [f for f in contract.functions if f.original_contract == contract]:
            if self.detect_suicidal_func(f):
                ret.append(f)
        return ret

    def _detect(self):
        """ Detect the suicidal functions
        """
        results = []
        for c in self.contracts:
            functions = self.detect_suicidal(c)
            for func in functions:

                txt = "{} ({}) allows anyone to destruct the contract\n"
                info = txt.format(func.canonical_name,
                                  func.source_mapping_str)

                json = self.generate_json_result(info)
                self.add_function_to_json(func, json)
                results.append(json)

        return results
