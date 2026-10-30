from slither.core.cfg.node import NodeType, Node
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.declarations import Contract, Function
from slither.core.solidity_types import ElementaryType
from slither.utils.output import Output
from slither.slithir.operations import Call, InternalCall, OperationWithLValue
from slither.core.variables.state_variable import StateVariable

Result = list[tuple[Node, list[str]]]


def detect_costly_operations_in_loop(contract: Contract) -> Result:
    ret: Result = []
    for f in contract.functions_entry_points:
        if f.is_implemented:
            costly_operations_in_loop(f.entry_point, 0, [], [], ret)

    return ret


def costly_operations_in_loop(
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

    if in_loop_counter > 0:
        for ir in node.irs:
            # Ignore Array/Mapping/Struct types for now
            if isinstance(ir, OperationWithLValue) and isinstance(ir.lvalue, StateVariable):
                ret.append((ir.node, calls_stack.copy()))
                break
            if isinstance(ir, (InternalCall)) and ir.function:
                calls_stack.append(node.function.canonical_name)
                costly_operations_in_loop(
                    ir.function.entry_point, in_loop_counter, visited, calls_stack, ret
                )
                calls_stack.pop()

    for son in node.sons:
        costly_operations_in_loop(son, in_loop_counter, visited, calls_stack, ret)


def cacheable_accumulators(function: Function, loop_writes: set[Node]) -> list[StateVariable]:
    """Identify scalar accumulators whose intermediate storage writes cannot be observed."""
    if (
        function.contains_assembly
        or function.modifiers
        or sum(n.type is NodeType.STARTLOOP for n in function.nodes) != 1
        or any(n.type is NodeType.RETURN for n in function.nodes)
        or any(isinstance(ir, Call) for n in function.nodes for ir in n.irs)
    ):
        return []
    candidates = []
    for variable in function.state_variables_written:
        if not variable.is_stored or not isinstance(variable.type, ElementaryType):
            continue
        if variable.type.storage_size[1]:
            continue
        updates = {n for n in function.nodes if variable in n.state_variables_written}
        reads = {n for n in function.nodes if variable in n.state_variables_read}
        if updates and updates <= loop_writes and reads == updates:
            candidates.append(variable)
    return sorted(candidates, key=lambda v: v.canonical_name)


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

    WIKI_RECOMMENDATION = (
        "Consider a local accumulator of the same type and a write immediately after loop exit "
        "only when intermediate state cannot be observed. Preserve arithmetic, break/continue "
        "and zero-iteration behavior. The optional cacheable_accumulators JSON field identifies "
        "conservative scalar candidates without calls, assembly, modifiers, nested loops or returns."
    )

    def _detect(self) -> list[Output]:
        """"""
        results: list[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_costly_operations_in_loop(c)
            loop_writes = {node for node, _ in values}
            cacheable = {
                function: cacheable_accumulators(function, loop_writes)
                for function in {node.function for node, _ in values}
            }
            for node, calls_stack in values:
                func = node.function
                info: DETECTOR_INFO = [func, " has costly operations inside a loop:\n"]
                info += ["\t- ", node, "\n"]

                if len(calls_stack) > 0:
                    info.append("\tCalls stack containing the loop:\n")
                    for call in calls_stack:
                        info.extend(["\t\t", call, "\n"])

                accumulators = [
                    v.name for v in cacheable[func] if v in node.state_variables_written
                ]
                fields = {"cacheable_accumulators": accumulators} if accumulators else None
                res = self.generate_result(info, fields)
                results.append(res)

        return results
