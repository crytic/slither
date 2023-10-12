"""
Module detecting incorrect operator usage for exponentiation where bitwise xor '^' is used instead of '**'
"""
from typing import Tuple, List, Union

from slither.core.cfg.node import Node
from slither.core.declarations import Contract, Function
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import Binary, BinaryType, Operation
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant
from slither.utils.output import Output


def _is_constant_candidate(var: Union[RVALUE, Function]) -> bool:
    """
    Check if the variable is a constant.
    Do not consider variable that are expressed with hexadecimal.
    Something like 2^0xf is likely to be a correct bitwise operator
    :param var:
    :return:
    """
    return isinstance(var, Constant) and not var.original_value.startswith("0x")


def _is_bitwise_xor_on_constant(ir: Operation) -> bool:
    return (
        isinstance(ir, Binary)
        and ir.type == BinaryType.CARET
        and (_is_constant_candidate(ir.variable_left) or _is_constant_candidate(ir.variable_right))
    )


def _detect_incorrect_operator(contract: Contract) -> List[Tuple[Function, Node]]:
    ret: List[Tuple[Function, Node]] = []
    f: Function
    for f in contract.functions + contract.modifiers:  # type:ignore
        # Heuristic: look for binary expressions with ^ operator where at least one of the operands is a constant, and
        # the constant is not in hex, because hex typically is used with bitwise xor and not exponentiation
        nodes = [node for node in f.nodes for ir in node.irs if _is_bitwise_xor_on_constant(ir)]
        for node in nodes:
            ret.append((f, node))
    return ret


# pylint: disable=too-few-public-methods
class IncorrectOperatorExponentiation(AbstractDetector):
    """
    Incorrect operator usage of bitwise xor mistaking it for exponentiation
    """

    ARGUMENT = "incorrect-exp"
    HELP = "Incorrect exponentiation"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#incorrect-exponentiation"

    WIKI_TITLE = "Incorrect exponentiation"
    WIKI_DESCRIPTION = "Detect use of bitwise `xor ^` instead of exponential `**`"
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Bug{
    uint UINT_MAX = 2^256 - 1;
    ...
}
```
Alice deploys a contract in which `UINT_MAX` incorrectly uses `^` operator instead of `**` for exponentiation"""

    WIKI_RECOMMENDATION = "Use the correct operator `**` for exponentiation."

    def _detect(self) -> List[Output]:
        """Detect the incorrect operator usage for exponentiation where bitwise xor ^ is used instead of **

        Returns:
            list: (function, node)
        """
        results: List[Output] = []
        for c in self.compilation_unit.contracts_derived:
            res = _detect_incorrect_operator(c)
            for (func, node) in res:
                info: DETECTOR_INFO = [
                    func,
                    " has bitwise-xor operator ^ instead of the exponentiation operator **: \n",
                ]
                info += ["\t - ", node, "\n"]
                results.append(self.generate_result(info))

        return results
