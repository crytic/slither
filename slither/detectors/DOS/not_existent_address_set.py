from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations import Assignment
from slither.slithir.variables import Constant
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class NotExistentAddress_set(AbstractDetector):

    ARGUMENT = "adress-not-exist-set"
    HELP = "if the address is wrong, the contract fails"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#adress-not-exist-set"

    WIKI_TITLE = "Not Existent Address - set"
    WIKI_DESCRIPTION = "If the address is wrong, the contract fails."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

address public owner;

constructor() public  {
    owner = 0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed;
    rate = 0;
    cap = 0;
}
The call fails when the address with which it interacts does not exist or when a contract exception occurs. 
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Set a function to modify the address."

    def detect_address(self, f):
        var = None
        state_variables = f.state_variables_written
        parameters = f.parameters

        for node in f.nodes:
            for ir in node.irs:
                if isinstance(ir, Assignment):
                    if (ir.lvalue in state_variables and
                        isinstance(ir.lvalue.type, ElementaryType) and
                        ir.lvalue.type == ElementaryType("address")
                        ):
                            if isinstance(ir.rvalue, Constant) or ir.rvalue in parameters:
                                #have set second address
                                if var != None:
                                    return []
                                var= ir.lvalue
                            
                            if ir.rvalue == SolidityVariableComposed("msg.sender") and var != None:
                                return []
        return var

    #check have a function to modify the address.
    def check_safe(self, var, functions):
        for f in functions:
            if var in f.state_variables_written:
                return False
        return var


    def _detect(self):
        """"""
        results = []
        const = None
        func = []
        var = []

        for c in self.contracts:
            for f in c.functions:
                if f.is_constructor:
                    const = f
                else:
                    func.append(f)
            if const:
                var = self.detect_address(const)
                var = self.check_safe(var, func)

            if not var:
                continue

            info = [var, " maybe a unexist address, and have no function to modify it.\n",]
            res = self.generate_result(info)
            results.append(res)

        return results
