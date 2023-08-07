"""
Module detecting unused return values from low level
"""
from typing import List

from slither.core.cfg.node import Node
from slither.slithir.operations import LowLevelCall

from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class UncheckedLowLevel(AbstractDetector):
    """
    If the return value of a low-level call is not checked, it might lead to losing ether
    """

    ARGUMENT = "unchecked-lowlevel"
    HELP = "Unchecked low-level calls"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-low-level-calls"

    WIKI_TITLE = "Unchecked low-level calls"
    WIKI_DESCRIPTION = "The return value of a low-level call is not checked."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MyConc{
    function my_func(address payable dst) public payable{
        dst.call.value(msg.value)("");
    }
}
```
The return value of the low-level call is not checked, so if the call fails, the Ether will be locked in the contract.
If the low level is used to prevent blocking operations, consider logging failed calls.
    """
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Ensure that the return value of a low-level call is checked or logged."

    @staticmethod
    def detect_unused_return_values(f: FunctionContract) -> List[Node]:
        """
        Return the nodes where the return value of a call is unused
        Args:
            f (Function)
        Returns:
            list(Node)
        """
        values_returned = []
        nodes_origin = {}
        for n in f.nodes:
            for ir in n.irs:
                if isinstance(ir, LowLevelCall):
                    # if a return value is stored in a state variable, it's ok
                    if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                        values_returned.append(ir.lvalue)
                        nodes_origin[ir.lvalue] = ir

                for read in ir.read:
                    if read in values_returned:
                        values_returned.remove(read)

        return [nodes_origin[value].node for value in values_returned]

    def _detect(self) -> List[Output]:
        """Detect low level calls where the success value is not checked"""
        results = []
        for c in self.compilation_unit.contracts_derived:
            for f in c.functions_and_modifiers:
                unused_return = UncheckedLowLevel.detect_unused_return_values(f)
                if unused_return:

                    for node in unused_return:
                        info: DETECTOR_INFO = [f, " ignores return value by ", node, "\n"]

                        res = self.generate_result(info)

                        results.append(res)

        return results
