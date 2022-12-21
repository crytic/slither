"""
Module detecting likelihood of price manipulation.

"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

from slither.slithir.operations.high_level_call import HighLevelCall
from slither.slithir.operations.binary import Binary
from slither.slithir.operations.assignment import Assignment
from slither.slithir.operations.binary import BinaryType
from slither.slithir.operations.return_operation import Return
from slither.slithir.operations.library_call import LibraryCall


class PriceManipulation(AbstractDetector):
    """
    Detect likelihood of price manipulation
    """

    ARGUMENT = "price-manipulation"
    HELP = "Spot price is vulnerable to price manipulation"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#price-manipulation"
    WIKI_TITLE = "PRICE_MANIPULATION"
    WIKI_DESCRIPTION = "PRICE_MANIPULATION"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
interface IERC20{
    function balanceOf(address) view external returns(uint);
}
contract A{
    IERC20 tokenA;
    IERC20 tokenB;
    address _lpaddr;

    function getprice() public view returns (uint256 _price) {
        uint256 lpTokenA=tokenA.balanceOf(_lpaddr); 
        uint256 lpTokenB=tokenB.balanceOf(_lpaddr); 
        _price = lpTokenA * 10**18 / lpTokenB;
    }
}
```
Attacker can easily manipulate _price.
https://github.com/rkm0959/rkm0959_presents/blob/main/PriceOracle-CODEGATE2022.pdf
"""
    WIKI_RECOMMENDATION = "Check whether price oracle uses spot price"

    def dfs(self, node):
        if node in self.visited:
            return False

        self.visited[node] = True

        if node in self.checked:
            return True

        if node not in self.tmp:
            return False

        ret = False
        for next in self.tmp[node]:
            ret = ret or self.dfs(next)

        return ret

    def _detect(self):

        results = []
        tmp = []

        for contract in self.compilation_unit.contracts:
            for function in contract.functions:
                self.tmp = {}
                self.checked = {}

                for node in function.nodes:
                    for ir in node.irs:

                        if isinstance(ir, HighLevelCall):
                            if "balanceOf".lower() in str(ir.function_name).lower():
                                self.checked[ir._lvalue] = True

                        # check return value of balanceOf is used to arithmetic operation.
                        if isinstance(ir, Binary) and ir._type in [
                            BinaryType.DIVISION,
                            BinaryType.MULTIPLICATION,
                            BinaryType.ADDITION,
                            BinaryType.SUBTRACTION,
                        ]:
                            self.tmp[ir._lvalue] = ir.read
                            self.visited = {}
                            if self.dfs(ir._lvalue):
                                tmp.append(function)

                        # safemath
                        if isinstance(ir, LibraryCall):
                            if "math".lower() in str(ir.destination).lower():
                                self.tmp[ir._lvalue] = ir.arguments
                                self.visited = {}
                                if self.dfs(ir._lvalue):
                                    tmp.append(function)

                        if isinstance(ir, Assignment):
                            self.tmp[ir._lvalue] = [ir._rvalue]
                            self.visited = {}
                            if self.dfs(ir._lvalue):
                                tmp.append(function)

                        if isinstance(ir, Return):
                            self.visited = {}
                            if self.dfs(ir.read[0]):
                                self.visited = {}
                                tmp.append(function)
        tmp = set(tmp)
        for function in tmp:
            info = [
                "Vulnerable to price manipulation via balanceOf in ",
                function,
                "\n",
            ]
            res = self.generate_result(info)
            results.append(res)
        return results
