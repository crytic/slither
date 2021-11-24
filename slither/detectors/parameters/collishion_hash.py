from collections import defaultdict
from slither.core.declarations.solidity_variables import SolidityFunction
from slither.core.solidity_types.array_type import ArrayType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import SolidityCall


class HashCollision(AbstractDetector):

    ARGUMENT = "hash-collision"
    HELP = "using abi.encodePacked() with multiple variable-length parameters can cause hash collisions"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#hash-collision"

    WIKI_TITLE = "Hash Collision"
    WIKI_DESCRIPTION = " In some cases, using abi.encodePacked() with multiple variable-length parameters can cause hash collisions."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

function addUsers(
        address[] calldata admins,
        address[] calldata regularUsers,
    )
        external
    {
        bytes32 hash = keccak256(abi.encodePacked(admins, regularUsers));
    }
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Don't use multiple variable-length parameters"

    @staticmethod
    def detect_continue(f):
        bugs = defaultdict(list)
        res = []

        hash_functions = [
            SolidityFunction("keccak256()"), 
            SolidityFunction("keccak256(bytes)"),
            SolidityFunction("sha256()"),
            SolidityFunction("sha256(bytes)"),
            SolidityFunction("sha3()"),
            SolidityFunction("ripemd160()"),
            SolidityFunction("ripemd160(bytes)"),
            ]

        for node in f.nodes:
            for ir in node.irs:
                if isinstance(ir, SolidityCall):
                    if ir.function == SolidityFunction("abi.encodePacked()"):
                        count = 0
                        for para in ir.arguments:
                            if isinstance(para.type, ArrayType):
                                count += 1
                        
                        if count > 1:
                            bugs[ir.lvalue] = node
                    
                    elif (ir.function in hash_functions and
                        len(ir.arguments) == 1 and 
                        ir.arguments[0] in bugs
                    ):
                        res.append(bugs[ir.arguments[0]])

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
                    info = [var, " can cause hash collisions.\n",]

                    res = self.generate_result(info)
                    results.append(res)

        return results
