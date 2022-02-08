from typing import List
from slither.core.cfg.node import NodeType, Node
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.declarations import Contract
from slither.utils.output import Output
from slither.slithir.operations import InternalCall, OperationWithLValue
from slither.core.variables.state_variable import StateVariable


def detect_costly_operations_in_loop(contract: Contract) -> List[Node]:
    ret: List[Node] = []
    for f in contract.functions_entry_points:
        if f.is_implemented:
            costly_operations_in_loop(f.entry_point, 0, [], ret)

    return ret


def costly_operations_in_loop(
    node: Node, in_loop_counter: int, visited: List[Node], ret: List[Node]
) -> None:
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
            # Ignore Array/Mapping/Struct types for now
            if isinstance(ir, OperationWithLValue) and isinstance(ir.lvalue, StateVariable):
                ret.append(ir.node)
                break
            if isinstance(ir, (InternalCall)):
                costly_operations_in_loop(ir.function.entry_point, in_loop_counter, visited, ret)

    for son in node.sons:
        costly_operations_in_loop(son, in_loop_counter, visited, ret)


class CostlyOperationsInLoop(AbstractDetector):

    ARGUMENT = "costly-loop"
    HELP = "Costly operations in a loop"
    IMPACT = DetectorClassification.INFORMATIONAL
    # Overall the detector seems precise, but it does not take into account
    # case where there are external calls or internal calls that might read the state
    # variable changes. In these cases the optimization should not be applied
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#costly-operations-inside-a-loop"

    WIKI_TITLE = "Costly operations inside a loop"
    WIKI_DESCRIPTION = (
        "Costly operations inside a loop might waste gas, so optimizations are justified."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract CostlyOperationsInLoop{

    uint loop_count = 100;
    uint state_variable=0;

    function bad() external{
        for (uint i=0; i < loop_count; i++){
            state_variable++;
        }
    }

    function good() external{
      uint local_variable = state_variable;
      for (uint i=0; i < loop_count; i++){
        local_variable++;
      }
      state_variable = local_variable;
    }
}
```
Incrementing `state_variable` in a loop incurs a lot of gas because of expensive `SSTOREs`, which might lead to an `out-of-gas`."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Use a local variable to hold the loop computation result."

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_costly_operations_in_loop(c)
            for node in values:
                func = node.function
                info = [func, " has costly operations inside a loop:\n"]
                info += ["\t- ", node, "\n"]
                res = self.generate_result(info)
                results.append(res)

        return results
