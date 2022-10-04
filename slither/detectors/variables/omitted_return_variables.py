"""
Module detecting "Omitted Return Variables"
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType

class OmittedReturnVariables(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'variable-omitted'
    HELP = 'Omitted Return Variables'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#omitted-return-variables"

    WIKI_TITLE = 'Omitted Return Variables'
    WIKI_DESCRIPTION = 'Detects when return function omits to return the declared return variables.'

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """"
```solidity
pragma solidity ^0.8.0;

contract Bug {
    function omitted() external view returns(uint val) {
        val = 1;
        return 0;
    } //returns 0
}
```"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """Return declared return variables."""

    ERR = {}
    INFO = []

    def info(self): #3/3 (end) ↰
        if len(self.ERR)>0:
            result = []
            for bug_location, omitted_var_pairs in self.ERR.items():
                result.append(bug_location)
                result.append(' has an omitted return variable/s:\n• ')
                for declared, returned in omitted_var_pairs:
                    result.append('declared: ')
                    left = len(declared)
                    for var in declared:
                        result.append(var)
                        if left>1: result.append(', ')
                        left-=1
                    result.append('\n• returned: ')
                    result.append(returned)
                result.append('\n')
            self.INFO.append(self.generate_result(result))
        return self.INFO

    def detect_omitted(self, return_vars, function): #2/3 ↑
        omitted_pairs = []
        for node in function.nodes:
            if node.type==NodeType.RETURN and node.variables_read!=return_vars:
                omitted_pairs.append([return_vars, node])
        return omitted_pairs

    def get_return_vars_from(self, function): #1/3 ↑
        return_vars_names = []
        for var in function.returns:
            if var.name=='': return [] #ignore unnamed
            return_vars_names.append(var)
        return return_vars_names

    def _detect(self): # 0/3 (start) ⤴
        for contract in self.contracts:
            if contract.is_interface: continue #ignore interfaces
            for function in contract.functions:
                if function.return_type and len(function.nodes)>0: #ignore inherited interfaces
                    return_vars = self.get_return_vars_from(function)
                    if return_vars:
                        omitted_return_vars = self.detect_omitted(return_vars, function)
                        if omitted_return_vars:
                            self.ERR[function] = omitted_return_vars
        return self.info()