"""
Module detecting shadowing variables on abstract contract
Recursively check the called functions
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils import json_utils


class ShadowingAbstractDetection(AbstractDetector):
    """
    Shadowing detection
    """

    ARGUMENT = 'shadowing-abstract'
    HELP = 'State variables shadowing from abstract contracts'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#state-variable-shadowing-from-abstract-contracts'


    WIKI_TITLE = 'State variable shadowing from abstract contracts'
    WIKI_DESCRIPTION = 'Detection of state variables shadowed from abstract contracts.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract BaseContract{
    address owner;
}

contract DerivedContract is BaseContract{
    address owner;
}
```
`owner` of `BaseContract` is shadowed in `DerivedContract`.'''

    WIKI_RECOMMENDATION = 'Remove the state variable shadowing.'


    def detect_shadowing(self, contract):
        ret = []
        variables_fathers = []
        for father in contract.inheritance:
            if all(not f.is_implemented for f in father.functions + father.modifiers):
                variables_fathers += father.state_variables_declared

        for var in contract.state_variables_declared:
            shadow = [v for v in variables_fathers if v.name == var.name]
            if shadow:
                ret.append([var] + shadow)
        return ret


    def _detect(self):
        """ Detect shadowing

        Recursively visit the calls
        Returns:
            list: {'vuln', 'filename,'contract','func', 'shadow'}

        """
        results = []
        for c in self.contracts:
            shadowing = self.detect_shadowing(c)
            if shadowing:
                for all_variables in shadowing:
                    shadow = all_variables[0]
                    variables = all_variables[1:]
                    info = '{} ({}) shadows:\n'.format(shadow.canonical_name,
                                                       shadow.source_mapping_str)
                    for var in variables:
                        info += "\t- {} ({})\n".format(var.canonical_name,
                                                       var.source_mapping_str)

                    json = self.generate_json_result(info)
                    json_utils.add_variables_to_json(all_variables, json)
                    results.append(json)

        return results
