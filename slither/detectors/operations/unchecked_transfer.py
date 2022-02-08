"""
Module detecting unused transfer/transferFrom return values from external calls
"""

from slither.core.declarations import Function
from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.operations.unused_return_values import UnusedReturnValues
from slither.slithir.operations import HighLevelCall


class UncheckedTransfer(UnusedReturnValues):
    """
    If the return value of a transfer/transferFrom function is never used, it's likely to be bug
    """

    ARGUMENT = "unchecked-transfer"
    HELP = "Unchecked tokens transfer"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-transfer"

    WIKI_TITLE = "Unchecked transfer"
    WIKI_DESCRIPTION = "The return value of an external transfer/transferFrom call is not checked"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Token {
    function transferFrom(address _from, address _to, uint256 _value) public returns (bool success);
}
contract MyBank{  
    mapping(address => uint) balances;
    Token token;
    function deposit(uint amount) public{
        token.transferFrom(msg.sender, address(this), amount);
        balances[msg.sender] += amount;
    }
}
```
Several tokens do not revert in case of failure and return false. If one of these tokens is used in `MyBank`, `deposit` will not revert if the transfer fails, and an attacker can call `deposit` for free.."""
    # endregion wiki_exploit_scenariox

    WIKI_RECOMMENDATION = (
        "Use `SafeERC20`, or ensure that the transfer/transferFrom return value is checked."
    )

    def _is_instance(self, ir):  # pylint: disable=no-self-use
        return (
            isinstance(ir, HighLevelCall)
            and isinstance(ir.function, Function)
            and ir.function.solidity_signature
            in ["transfer(address,uint256)", "transferFrom(address,address,uint256)"]
        )
