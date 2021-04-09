"""
Module detecting unused transfer/transferFrom return values from external calls
"""

from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import HighLevelCall
from slither.core.declarations import Function


class UnusedReturnValuesTransfers(AbstractDetector):
    """
    If the return value of a transfer/transferFrom function is never used, it's likely to be bug
    """

    ARGUMENT = "unused-return-transfers"
    HELP = "Unused transfer/transferFrom return values"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-return-transfers"

    WIKI_TITLE = "Unused return transfers"
    WIKI_DESCRIPTION = "The return value of an external transfer/transferFrom call is not used"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Token {
    function transfer(address _to, uint256 _value) public returns (bool success);
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success);
}
contract MyConc{  
    function my_func1(Token tok, address to) public{
        tok.transfer(to, 1 ether);
    }
    function my_func2(Token tok, address to) public{
        tok.transferFrom(address(this), to, 1 ether);
    }
}
```
`MyConc` calls `transfer` or `transferFrom` on a token contract but does not check the return value. As a result, transfers that do not revert on failure will appear to have succeeded."""

    WIKI_RECOMMENDATION = "Ensure that the returned boolean of all transfer and transferFrom function calls is checked."

    _txt_description = "external transfer calls"

    def _is_instance(self, ir):  # pylint: disable=no-self-use
        return (
            isinstance(ir, HighLevelCall)
            and isinstance(ir.function, Function)
            and ir.function.solidity_signature
            in ["transfer(address,uint256)", "transferFrom(address,address,uint256)"]
        )

    def detect_unused_return_values(self, f):  # pylint: disable=no-self-use
        """
            Return the nodes where the return value of a call is unused
        Args:
            f (Function)
        Returns:
            list(Node)
        """
        values_returned = []
        nodes_origin = {}
        for n in f.nodes:
            for ir in n.irs:
                if self._is_instance(ir):
                    # if a return value is stored in a state variable, it's ok
                    if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                        values_returned.append(ir.lvalue)
                        nodes_origin[ir.lvalue] = ir
                for read in ir.read:
                    if read in values_returned:
                        values_returned.remove(read)

        return [nodes_origin[value].node for value in values_returned]

    def _detect(self):
        """Detect external transfer/transferFrom calls whose return value is not checked"""
        results = []
        for c in self.slither.contracts:
            for f in c.functions + c.modifiers:
                if f.contract_declarer != c:
                    continue
                unused_return = self.detect_unused_return_values(f)
                if unused_return:

                    for node in unused_return:
                        info = [f, " ignores return value of ", node, "\n"]

                        res = self.generate_result(info)

                        results.append(res)

        return results
