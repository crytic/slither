"""
Module detecting "Unnamed Return Shadows Local"
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import NodeType

class UnnamedReturnShadowsLocal(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'shadowing-return-unnamed'
    HELP = 'Unnamed Return Shadows Local'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unnamed-return-shadows-local"

    WIKI_TITLE = 'Unnamed Return Shadows Local'
    WIKI_DESCRIPTION = "Detects when return function without `return` statement has unnamed variables inside `returns`."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """"
```solidity
pragma solidity ^0.8.0;

contract Bug {
    function unnamed() external view returns(uint) {
        uint val = 1;
    } //returns 0
}
```"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
    1. Name return variables inside "returns(...)".
    2. Add a `return` statement at the end of the function."""

    ERR  = {}
    INFO = []

    def info(self): #3/3 (end) ↰
        if len(self.ERR)>0:
            result = []
            for bug_location, unnamed_vars in self.ERR.items():
                result.append(bug_location)
                result.append(" does not have `return` and inside `returns` has unnamed variable/s:\n• ")
                vars_left = len(unnamed_vars)
                for var in unnamed_vars:
                    result.append(f'"{var.type}" ')
                    result.append(var)
                    if vars_left>1: result.append('\n• ')
                    vars_left-=1
                result.append('\n')
            self.INFO.append(self.generate_result(result))
        return self.INFO

    def detect_unnamed_return_vars(self, function): #2/3 ↑
        unnamed_return_vars = []

        for var in function.returns:
            if var.name=='':
                unnamed_return_vars.append(var)
        return unnamed_return_vars

    def no_return_statement_in(self, function): #1/3 ↑
        if len(function.nodes)==0: return False #ignore inherited interfaces
        for node in function.nodes:
            if node.type==NodeType.RETURN:
                return False
        return True

    def _detect(self): # 0/3 (start) ⤴
        for contract in self.contracts:
            if contract.is_interface: continue #ignore interfaces
            for function in contract.functions:
                if function.return_type and self.no_return_statement_in(function):
                                # ↓↓↓ error-potential zone ↓↓↓ #
                    unnamed_return_vars = self.detect_unnamed_return_vars(function)
                    if unnamed_return_vars:
                        self.ERR[function] = unnamed_return_vars
        return self.info()