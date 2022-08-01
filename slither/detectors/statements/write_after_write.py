from typing import List, Set, Tuple, Dict

from slither.core.cfg.node import Node, NodeType
from slither.core.solidity_types import ElementaryType
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import (
    OperationWithLValue,
    HighLevelCall,
    InternalDynamicCall,
    InternalCall,
    LowLevelCall,
    Operation,
)
from slither.slithir.variables import ReferenceVariable, TemporaryVariable, TupleVariable
from slither.slithir.variables.variable import SlithIRVariable


def _remove_states(written: Dict[Variable, Node]):
    for key in list(written.keys()):
        if isinstance(key, StateVariable):
            del written[key]


def _handle_ir(
    ir: Operation,
    written: Dict[Variable, Node],
    ret: List[Tuple[Variable, Node, Node]],
):
    if isinstance(ir, (HighLevelCall, InternalDynamicCall, LowLevelCall)):
        _remove_states(written)

    if isinstance(ir, InternalCall):
        if ir.function.all_high_level_calls() or ir.function.all_library_calls():
            _remove_states(written)

        all_read = ir.function.all_state_variables_read()
        for read in all_read:
            if (
                isinstance(read, Variable)
                and isinstance(read.type, ElementaryType)
                and not isinstance(read, SlithIRVariable)
                and read in written
            ):
                del written[read]

    for read in ir.read:
        if (
            isinstance(read, Variable)
            and isinstance(read.type, ElementaryType)
            and not isinstance(read, SlithIRVariable)
            and read in written
        ):
            del written[read]

    if isinstance(ir, OperationWithLValue):
        # Until we have a better handling of mapping/array we only look for simple types
        if (
            ir.lvalue
            and isinstance(ir.lvalue.type, ElementaryType)
            and not isinstance(ir.lvalue, (ReferenceVariable, TemporaryVariable, TupleVariable))
        ):
            if ir.lvalue.name == "_":
                return
            if ir.lvalue in written:
                ret.append((ir.lvalue, written[ir.lvalue], ir.node))
            written[ir.lvalue] = ir.node


def _detect_write_after_write(
    node: Node,
    explored: Set[Node],
    written: Dict[Variable, Node],
    ret: List[Tuple[Variable, Node, Node]],
):
    if node in explored:
        return

    explored.add(node)

    # We could report write after write for, but this lead to a lot of FP due to the initilization to zero pattern:
    # uint a = 0;
    # a = 10;
    # To do better, we could filter out if the variable is init to zero
    if node.type != NodeType.VARIABLE:
        for ir in node.irs:
            _handle_ir(ir, written, ret)

    if len(node.sons) > 1:
        written = {}
    for son in node.sons:
        _detect_write_after_write(son, explored, dict(written), ret)


class WriteAfterWrite(AbstractDetector):
    ARGUMENT = "write-after-write"
    HELP = "Unused write"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#write-after-write"

    WIKI_TITLE = "Write after write"
    WIKI_DESCRIPTION = """Detects variables that are written but never read and written again."""

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    ```solidity
    contract Buggy{
        function my_func() external initializer{
            // ...
            a = b;
            a = c;
            // ..
        }
    }
    ```
    `a` is first asigned to `b`, and then to `c`. As a result the first write does nothing."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """Fix or remove the writes."""

    def _detect(self):
        results = []

        for contract in self.compilation_unit.contracts_derived:
            for function in contract.functions:
                if function.entry_point:
                    ret = []
                    _detect_write_after_write(function.entry_point, set(), {}, ret)
                    for var, node1, node2 in ret:
                        info = [var, " is written in both\n\t", node1, "\n\t", node2, "\n"]

                        res = self.generate_result(info)
                        results.append(res)

        return results
