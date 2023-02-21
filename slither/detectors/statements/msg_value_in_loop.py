from typing import List, Optional
from slither.core.cfg.node import NodeType, Node
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import InternalCall
from slither.core.declarations import SolidityVariableComposed, Contract
from slither.utils.output import Output


def detect_msg_value_in_loop(contract: Contract) -> List[Node]:
    results: List[Node] = []
    for f in contract.functions_entry_points:
        if f.is_implemented and f.payable:
            msg_value_in_loop(f.entry_point, 0, [], results)
    return results


def msg_value_in_loop(
    node: Optional[Node], in_loop_counter: int, visited: List[Node], results: List[Node]
) -> None:

    if node is None:
        return

    if node in visited:
        return
    # shared visited
    visited.append(node)

    if node.type == NodeType.STARTLOOP:
        in_loop_counter += 1
    elif node.type == NodeType.ENDLOOP:
        in_loop_counter -= 1

    for ir in node.all_slithir_operations():
        if in_loop_counter > 0 and SolidityVariableComposed("msg.value") in ir.read:
            results.append(ir.node)
        if isinstance(ir, (InternalCall)):
            msg_value_in_loop(ir.function.entry_point, in_loop_counter, visited, results)

    for son in node.sons:
        msg_value_in_loop(son, in_loop_counter, visited, results)


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
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
Track msg.value through a local variable and decrease its amount on every iteration/usage.
"""

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_msg_value_in_loop(c)
            for node in values:
                func = node.function

                info = [func, " use msg.value in a loop: ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
