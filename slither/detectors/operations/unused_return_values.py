"""
Module detecting unused return values from external calls
"""
from typing import List

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import HighLevelCall, Assignment, Unpack, Operation
from slither.slithir.variables import TupleVariable
from slither.utils.output import Output


class UnusedReturnValues(AbstractDetector):
    """
    If the return value of a function is never used, it's likely to be bug
    """

    ARGUMENT = "unused-return"
    HELP = "Unused return values"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unused-return"

    WIKI_TITLE = "Unused return"
    WIKI_DESCRIPTION = (
        "The return value of an external call is not stored in a local or state variable."
    )

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MyConc{
    using SafeMath for uint;   
    function my_func(uint a, uint b) public{
        a.add(b);
    }
}
```
`MyConc` calls `add` of `SafeMath`, but does not store the result in `a`. As a result, the computation has no effect."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Ensure that all the return values of the function calls are used."

    def _is_instance(self, ir: Operation) -> bool:  # pylint: disable=no-self-use
        return (
            isinstance(ir, HighLevelCall)
            and (
                (
                    isinstance(ir.function, Function)
                    and ir.function.solidity_signature
                    not in ["transfer(address,uint256)", "transferFrom(address,address,uint256)"]
                )
                or not isinstance(ir.function, Function)
            )
            or ir.node.type == NodeType.TRY
            and isinstance(ir, (Assignment, Unpack))
        )

    def detect_unused_return_values(
        self, f: FunctionContract
    ) -> List[Node]:  # pylint: disable=no-self-use
        """
            Return the nodes where the return value of a call is unused
        Args:
            f (Function)
        Returns:
            list(Node)
        """
        values_returned = []
        nodes_origin = {}
        # pylint: disable=too-many-nested-blocks
        for n in f.nodes:
            for ir in n.irs:
                if self._is_instance(ir):
                    # if a return value is stored in a state variable, it's ok
                    if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                        values_returned.append((ir.lvalue, None))
                        nodes_origin[ir.lvalue] = ir
                        if isinstance(ir.lvalue, TupleVariable):
                            # we iterate the number of elements the tuple has
                            # and add a (variable, index) in values_returned for each of them
                            for index in range(len(ir.lvalue.type)):
                                values_returned.append((ir.lvalue, index))
                for read in ir.read:
                    remove = (read, ir.index) if isinstance(ir, Unpack) else (read, None)
                    if remove in values_returned:
                        # this is needed to remove the tuple variable when the first time one of its element is used
                        if remove[1] is not None and (remove[0], None) in values_returned:
                            values_returned.remove((remove[0], None))
                        values_returned.remove(remove)
        return [nodes_origin[value].node for (value, _) in values_returned]

    def _detect(self) -> List[Output]:
        """Detect high level calls which return a value that are never used"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            for f in c.functions_and_modifiers:
                unused_return = self.detect_unused_return_values(f)
                if unused_return:

                    for node in unused_return:
                        info: DETECTOR_INFO = [f, " ignores return value by ", node, "\n"]

                        res = self.generate_result(info)

                        results.append(res)

        return results
