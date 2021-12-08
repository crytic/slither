from typing import List
from slither.core.cfg.node import NodeType, Node
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations import Contract
from slither.utils.output import Output
from slither.slithir.operations import (
    HighLevelCall,
    LibraryCall,
    LowLevelCall,
    Send,
    Transfer,
    InternalCall,
)


def detect_call_in_loop(contract: Contract) -> List[Node]:
    ret: List[Node] = []
    for f in contract.functions_entry_points:
        if f.is_implemented:
            call_in_loop(f.entry_point, 0, [], ret)

    return ret


def call_in_loop(node: Node, in_loop_counter: int, visited: List[Node], ret: List[Node]) -> None:
    if node in visited:
        return
    # shared visited
    visited.append(node)

    if node.type == NodeType.STARTLOOP:
        in_loop_counter += 1
    elif node.type == NodeType.ENDLOOP:
        in_loop_counter -= 1

    if in_loop_counter > 0:
        for ir in node.all_slithir_operations():
            if isinstance(ir, (LowLevelCall, HighLevelCall, Send, Transfer)):
                if isinstance(ir, LibraryCall):
                    continue
                ret.append(ir.node)
            if isinstance(ir, (InternalCall)):
                call_in_loop(ir.function.entry_point, in_loop_counter, visited, ret)

    for son in node.sons:
        call_in_loop(son, in_loop_counter, visited, ret)


class MultipleCallsInLoop(AbstractDetector):

    ARGUMENT = "calls-loop"
    HELP = "Multiple calls in a loop"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#calls-inside-a-loop"

    WIKI_TITLE = "Calls inside a loop"
    WIKI_DESCRIPTION = "Calls inside a loop might lead to a denial-of-service attack."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract CallsInLoop{

    address[] destinations;

    constructor(address[] newDestinations) public{
        destinations = newDestinations;
    }

    function bad() external{
        for (uint i=0; i < destinations.length; i++){
            destinations[i].transfer(i);
        }
    }

}
```
If one of the destinations has a fallback function that reverts, `bad` will always revert."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Favor [pull over push](https://github.com/ethereum/wiki/wiki/Safety#favor-pull-over-push-for-external-calls) strategy for external calls."

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_call_in_loop(c)
            for node in values:
                func = node.function

                info = [func, " has external calls inside a loop: ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
