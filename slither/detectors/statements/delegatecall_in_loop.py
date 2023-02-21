from typing import List, Optional
from slither.core.cfg.node import NodeType, Node
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall, InternalCall
from slither.core.declarations import Contract
from slither.utils.output import Output


def detect_delegatecall_in_loop(contract: Contract) -> List[Node]:
    results: List[Node] = []
    for f in contract.functions_entry_points:
        if f.is_implemented and f.payable:
            delegatecall_in_loop(f.entry_point, 0, [], results)
    return results


def delegatecall_in_loop(
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
        if (
            in_loop_counter > 0
            and isinstance(ir, (LowLevelCall))
            and ir.function_name == "delegatecall"
        ):
            results.append(ir.node)
        if isinstance(ir, (InternalCall)):
            delegatecall_in_loop(ir.function.entry_point, in_loop_counter, visited, results)

    for son in node.sons:
        delegatecall_in_loop(son, in_loop_counter, visited, results)


class DelegatecallInLoop(AbstractDetector):
    """
    Detect the use of delegatecall inside a loop in a payable function
    """

    ARGUMENT = "delegatecall-loop"
    HELP = "Payable functions using `delegatecall` inside a loop"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#payable-functions-using-delegatecall-inside-a-loop"

    WIKI_TITLE = "Payable functions using `delegatecall` inside a loop"
    WIKI_DESCRIPTION = "Detect the use of `delegatecall` inside a loop in a payable function."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract DelegatecallInLoop{

    mapping (address => uint256) balances;

    function bad(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            address(this).delegatecall(abi.encodeWithSignature("addBalance(address)", receivers[i]));
        }
    }

    function addBalance(address a) public payable {
        balances[a] += msg.value;
    } 

}
```
When calling `bad` the same `msg.value` amount will be accredited multiple times."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
Carefully check that the function called by `delegatecall` is not payable/doesn't use `msg.value`.
"""

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_delegatecall_in_loop(c)
            for node in values:
                func = node.function

                info = [func, " has delegatecall inside a loop in a payable function: ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
