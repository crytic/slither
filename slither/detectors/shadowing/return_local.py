"""
Module detecting "Return Shadows Local"
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
import re

class ReturnShadowsLocal(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = 'shadowing-return'
    HELP = 'Return Shadows Local'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#return-shadows-local"

    WIKI_TITLE = 'Return Shadows Local'
    WIKI_DESCRIPTION = 'Detects when `return` variables `shadows` self-related `local` variables.'

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """"
```solidity
pragma solidity ^0.8.0;

contract Bug {
    function shadowed() external view returns(uint value) {
        uint value = 1;
    } //returns 0

    function nonamed() external view returns(uint) {
        uint value = 1;
    } //returns 0
}
```"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
    1. Name return variables inside "returns(...)".
    2. Don't re-declare the type of return variables.
    3. Add a `return` statement at the end of the function."""

    def info(self, err_nonamed, err_shadowed): #4/4 (end) ↰
        info = []
        if len(err_nonamed)>0:
            info.append(self.generate_result('💥💥💥 DETECTED NONAMED RETURN VARIABLE 💥💥💥\n'))
            info_tmp=''
            for bug_location, nonamed_vars in err_nonamed.items():
                for var in nonamed_vars:
                    info_tmp+=f'\n      * "{var.type}"'
                info.append(self.generate_result([
                    '  * In: ', bug_location, '\n    * inside "returns(...)", set name for:', info_tmp, '\n'
                ]))
                info_tmp=''
        if len(err_shadowed)>0:
            info.append(self.generate_result('\n💥💥💥 DETECTED SHADOWED LOCAL VARIABLE 💥💥💥\n'))
            info_tmp=''
            for bug_location, shadow_var in err_shadowed.items():
                for var in shadow_var:
                    info_tmp+=f'\n    * from variable: "{var}"'
                    info_tmp+=f'\n     * remove type declaration: "{var.type}"'
                info.append(self.generate_result(['  * Inside: ', bug_location, info_tmp, '\n']))
                info_tmp = ''
        return info

    def detect_shadowed_local_vars(self, function): #3/4 ↑
        shadowed_local_vars = []

        for return_var in function.returns:
            for local_var in function.variables:
                try: # to prevent e.g. wrong format errors
                    #get shadowing info, e.g., from name_scope_0; extract _scope_0
                    scope_part = re.sub(f'^{return_var.name}', "", local_var.name)
                    #save "return_var" if shadows "local_var" (return_var=local_var without scope)
                    if re.search('^_scope_[0-9]$', scope_part):
                        shadowed_local_vars.append(return_var)
                except Exception as e:
                    print(e); continue

        return shadowed_local_vars

    def detect_nonamed_return_vars(self, function): #2/4 ↑
        nonamed_return_vars = []

        for var in function.returns:
            if str(var)=='':
                nonamed_return_vars.append(var)

        return nonamed_return_vars

    def no_return_statment_in(self, function): #1/4 ↑
        if len(function.nodes)==0: return False #ignore inherited interfaces
        for node in function.nodes:
            if function.nodes and str(node.type)=='RETURN':
                return False
        return True

    def _detect(self): # 0/4 (start) ⤴
        err_nonamed = {}; err_shadowed = {}

        for contract in self.contracts: #for function in contract.functions + contract.modifiers:
            if contract.is_interface: continue #ignore interfaces
            for function in contract.functions:
                if function.return_type and self.no_return_statment_in(function):
                                # ↓↓↓ error-potential zone ↓↓↓
                    nonamed_return_vars = self.detect_nonamed_return_vars(function)
                    if nonamed_return_vars:
                        err_nonamed[function] = nonamed_return_vars
                        continue #goto↓ after naming return vars

                    shadowed_local_vars = self.detect_shadowed_local_vars(function)
                    if shadowed_local_vars:
                        err_shadowed[function] = shadowed_local_vars

        return self.info(err_nonamed, err_shadowed)