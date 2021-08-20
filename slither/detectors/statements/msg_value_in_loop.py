from slither.core.cfg.node import NodeType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations import SolidityVariableComposed


def detect_msg_value_in_loop(contract):
    results = []
    for f in contract.functions + contract.modifiers:
        if f.is_implemented and f.payable:
            msg_value_in_loop(f.entry_point, False, [], results)
    return results


def msg_value_in_loop(node, in_loop, visited, results):
    if node in visited:
        return
    # shared visited
    visited.append(node)

    if node.type == NodeType.STARTLOOP:
        in_loop = True
    elif node.type == NodeType.ENDLOOP:
        in_loop = False

    if in_loop:
        for ir in node.all_slithir_operations():
            if SolidityVariableComposed("msg.value") in ir.read:
                results.append(node)

    for son in node.sons:
        msg_value_in_loop(son, in_loop, visited, results)


class MsgValueInLoop(AbstractDetector):
    """
    Detect the use of msg.value inside a loop
    """

    ARGUMENT = "msg-value-loop"
    HELP = "msg.value inside a loop"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#msgvalue-inside-a-loop"

    WIKI_TITLE = "`msg.value` inside a loop"
    WIKI_DESCRIPTION = "Detect the use of `msg.value` inside a loop."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MsgValueInLoop{

    mapping (address => uint256) balances;

    function bad(address[] memory receivers) public payable {
        for (uint256 i=0; i < receivers.length; i++) {
            balances[receivers[i]] += msg.value;
        }
    }

}
```
When calling `bad` the same `msg.value` amount will be accredited multiple times."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
Don't use `msg.value` inside a loop. 
If you need to use it inside a loop save the `msg.value` to a local variable and use it as a cache (subtract the amount used from it)
"""

    def _detect(self):
        """"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_msg_value_in_loop(c)
            for node in values:
                func = node.function

                info = [func, " use msg.value in a loop: ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
