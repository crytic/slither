from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.solidity_types import ElementaryType, ArrayType
from slither.slithir.operations import Binary, BinaryType, Send, Transfer
from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.variables.reference import ReferenceVariable


class NotExistentAddress_transfer(AbstractDetector):

    ARGUMENT = "adress-not-exist-transfer"
    HELP = "if the address is wrong, the contract fails"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#adress-not-exist-transfer"

    WIKI_TITLE = "Not Existent Address - transfer"
    WIKI_DESCRIPTION = "If the address is wrong, the contract fails."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

address payable[] private refundAddresses;
mapping (address => uint) public refunds;

function refundAll() public {
    for(uint256 x = 0; x < refundAddresses.length; x++) { 
        require(refundAddresses[x].send(refunds[refundAddresses[x]])); // doubly bad, 
    }
}
The call fails when the address with which it interacts does not exist, and failure on send will hold up all funds.
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Set a function to modify the address."   

    #check have a function to modify the address.
    def check_safe(self, f, address_array):
        exsist_address = []
        res = []

        for n in f.nodes:
            for ir in n.irs:
                if (isinstance(ir, Binary) and
                    ir.type in [BinaryType.EQUAL, BinaryType.NOT_EQUAL] and
                    SolidityVariableComposed("msg.sender") in ir.read
                ):
                    for v in address_array:
                        print(address_array)
                        if is_dependent(ir.lvalue, v, f.contract):
                            exsist_address.append(v)
                
                elif isinstance(ir, Send) or isinstance(ir, Transfer):
                    if (isinstance(ir.destination, ReferenceVariable) and
                        ir.destination.type not in exsist_address
                    ):
                        res.append(n)

        return res


    def _detect(self):
        """"""
        results = []
        const = None

        for c in self.contracts:
            state_array = [v for v in c.variables if isinstance(v.type, ArrayType)]
            state_address_array = [v for v in state_array if v.type.type == ElementaryType("address")]

            for f in c.functions_declared:
                vars  = self.check_safe(f, state_address_array)
                if not vars:
                    continue
                info = [f, " does not check address exist or not when transfer ethers.\n",]
                for var in vars:
                    info = [var, " not check the address exists or not.\n",]
                    res = self.generate_result(info)
                    results.append(res)

        return results
