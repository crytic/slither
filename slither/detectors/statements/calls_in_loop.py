from slither.core.cfg.node import NodeType, Node
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
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

Result = list[tuple[Node, list[str]]]


def detect_call_in_loop(contract: Contract) -> Result:
    ret: Result = []
    for f in contract.functions_entry_points:
        if f.is_implemented:
            call_in_loop(f.entry_point, 0, [], [], ret)

    return ret


def call_in_loop(
    node: Node | None,
    in_loop_counter: int,
    visited: list[Node],
    calls_stack: list[str],
    ret: Result,
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

    for ir in node.irs:
        if isinstance(ir, (LowLevelCall, HighLevelCall, Send, Transfer)) and in_loop_counter > 0:
            if isinstance(ir, LibraryCall):
                continue
            ret.append((ir.node, calls_stack.copy()))
        if isinstance(ir, (InternalCall)):
            assert ir.function
            calls_stack.append(node.function.canonical_name)
            call_in_loop(ir.function.entry_point, in_loop_counter, visited, calls_stack, ret)
            calls_stack.pop()

    for son in node.sons:
        call_in_loop(son, in_loop_counter, visited, calls_stack, ret)


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

    def _detect(self) -> list[Output]:
        """"""
        results: list[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_call_in_loop(c)
            for node, calls_stack in values:
                func = node.function

                info: DETECTOR_INFO = [func, " has external calls inside a loop: ", node, "\n"]

                if len(calls_stack) > 0:
                    info.append("\tCalls stack containing the loop:\n")
                    for call in calls_stack:
                        info.extend(["\t\t", call, "\n"])

                res = self.generate_result(info)
                results.append(res)

        return results
