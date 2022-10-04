"""
Module detecting "Return Shadows Local"
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType
import re

class ReturnShadowsLocal(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'shadowing-return-local'
    HELP = 'Return Shadows Local'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#return-shadows-local"

    WIKI_TITLE = 'Return Shadows Local'
    WIKI_DESCRIPTION = 'Detects when return function without `return` statement shadows self-related local variables.'

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """"
```solidity
pragma solidity ^0.8.0;

contract Bug {
    function shadowed() external view returns(uint val) {
        uint val = 1;
    } //returns 0
}
```"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
    1. Don't re-declare the type of return variables.
    2. Add a `return` statement at the end of the function."""

    ERR = {}
    INFO = []

    def info(self): #4/4 (end) ↰
        if len(self.ERR)>0:
            result = []
            for bug_location, shadower_shadowed_pair in self.ERR.items():
                result.append(bug_location)
                result.append(" does not have `return` and has its return variable/s:\n• ")
                pairs_left = len(shadower_shadowed_pair)
                for shadower, shadowed in shadower_shadowed_pair:
                    result.append(shadowed) #in local
                    result.append(' shadowed by ')
                    result.append(shadower) #from "returns(...)""
                    if pairs_left>1: result.append('\n• ')
                    pairs_left-=1
                result.append('\n')
            self.INFO.append(self.generate_result(result))
        return self.INFO

    def detect_shadower_shadowed_pair(self, function): #3/4 ↑
        shadower_shadowed_pairs = []

        for return_var in function.returns: #potentially shadower
            for local_var in function.variables: #potentially shadowed
                try: # to prevent e.g. wrong format errors
                    #get shadowing info, e.g., from "name_scope_0" extract "_scope_0"
                    scope_part = re.sub(f'^{return_var.name}', "", local_var.name)
                    #save "return_var" if shadows "local_var"
                    if re.search('^_scope_[0-9]$', scope_part):
                        shadower_shadowed_pairs.append([return_var, local_var])
                except Exception as e:
                    print(e); continue
        return shadower_shadowed_pairs

    def return_vars_named_in(self, function): #2/4 ↑
        for var in function.returns:
            if var.name=='':
                return False
        return True

    def no_return_statement_in(self, function): #1/3 ↑
        if len(function.nodes)==0: return False #ignore inherited interfaces
        for node in function.nodes:
            if node.type==NodeType.RETURN:
                return False
        return True

    def _detect(self): # 0/4 (start) ⤴
        for contract in self.contracts:
            if contract.is_interface: continue #ignore interfaces
            for function in contract.functions:
                if function.return_type and self.no_return_statement_in(function) and self.return_vars_named_in(function):
                                # ↓↓↓ error-potential zone ↓↓↓ #
                    shadower_shadowed_pairs = self.detect_shadower_shadowed_pair(function)
                    if shadower_shadowed_pairs: #[[shadowed, shadower], ...]
                        self.ERR[function] = shadower_shadowed_pairs
        return self.info()