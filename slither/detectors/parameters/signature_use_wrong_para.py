from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.solidity_types import ElementaryType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import SolidityCall, Binary, TypeConversion, BinaryType, Assignment
from slither.slithir.variables import Constant

class SigWrongPara(AbstractDetector):

    ARGUMENT = "sig-wrong-para"
    HELP = "signature use wrong parameters"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#sig-wrong-para"

    WIKI_TITLE = "Signature with Wrong Parameters"
    WIKI_DESCRIPTION = " "

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

function getMyMoney(address payable _id, bytes32 _hash, uint8 v, bytes32 r, bytes32 s) external returns(bool){
    if(_id != ecrecover(_hash, v, r, s))
        return false;
    _id.transfer(address(this).balance);
    return true;
}
```
If _id is 0x0, and part of (_hash, v, r, s) are wrong. ecrecover() return 0x0. So pass the check."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Check this _id's value or ecrecover()'s value."
    @staticmethod
    def detect_continue(f):
        zero = []
        check_zero = []
        ecrecover = []
        res = []

        for node in f.nodes:
            for ir in node.irs:
                if (isinstance(ir, TypeConversion) and
                    isinstance(ir.type, ElementaryType) and
                    ir.type == ElementaryType("address") and
                    isinstance(ir.variable, Constant) and
                    ir.variable == Constant("0")
                ):
                    zero.append(ir.lvalue)
                
                elif (isinstance(ir, SolidityCall) and
                    ir.function == SolidityFunction("ecrecover(bytes32,uint8,bytes32,bytes32)")
                ):
                    ecrecover.append(ir.lvalue)

                elif isinstance(ir, Assignment):
                    (L, R) = ir.variables
                    if R in zero:
                        zero.append(L)
                    if R in ecrecover:
                        ecrecover.append(L)

                elif (isinstance(ir, Binary) and
                    ir.type in [BinaryType.EQUAL, BinaryType.NOT_EQUAL]
                ):
                    (L, R) = ir.read
                        
                    if (isinstance(L.type, ElementaryType) and
                        L.type == ElementaryType("address")
                    ):
                        if (R in zero or 
                            (isinstance(R, Constant) and
                            R == Constant("0"))
                        ):
                            check_zero.append(L)

                    elif (isinstance(R.type, ElementaryType) and
                        R.type == ElementaryType("address")
                    ):
                        if (L in zero or 
                            (isinstance(L, Constant) and
                            L == Constant("0"))
                        ):
                            check_zero.append(R)

                    if (L in ecrecover and 
                        L not in check_zero and
                        R not in check_zero
                    ):
                        if (isinstance(R.type, ElementaryType) and
                            R.type == ElementaryType("address")
                        ):
                            res.append(node)
                    
                    elif (R in ecrecover and 
                        R not in check_zero and
                        L not in check_zero
                    ):
                        
                        if (isinstance(L.type, ElementaryType) and
                            L.type == ElementaryType("address")
                        ):
                            res.append(node)                
                


        return res


    def _detect(self):
        """"""
        results = []

        for c in self.contracts:
            for f in c.functions_declared:
                values = self.detect_continue(f)
            
                if not values:
                    continue
                
                for var in values:
                    info = [var, " dosn't check this value is 0 or not.\n",]

                    res = self.generate_result(info)
                    results.append(res)

        return results
