from typing import List
from slither.core.cfg.node import Node
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import Binary, BinaryType, SolidityCall, Member
from slither.core.declarations import SolidityVariableComposed, Contract
from slither.utils.output import Output
from slither.slithir.variables import Constant


def detect_sender_checked_origin(contract: Contract) -> List[Node]:
    results: List[Node] = []
    for f in contract.functions_and_modifiers:
        if (
            SolidityVariableComposed("msg.sender") in f.solidity_variables_read
            and SolidityVariableComposed("tx.origin") in f.solidity_variables_read
        ):
            for n in f.nodes:
                if n.is_conditional():
                    has_sender_eq_origin = False
                    has_sender_eq_zero = False
                    ref_code_call = None  # track the reference to the SolidityCall code()
                    ref_length_access = None  # track the reference when accessing the code length

                    for ir in n.irs:
                        if (
                            isinstance(ir, Binary)
                            and ir.type == BinaryType.EQUAL
                            and SolidityVariableComposed("tx.origin") in ir.read
                            and SolidityVariableComposed("msg.sender") in ir.read
                        ):
                            has_sender_eq_origin = True
                        elif (
                            isinstance(ir, Binary)
                            and ir.type == BinaryType.EQUAL
                            and Constant("0") in ir.read
                            and ref_length_access in ir.read
                        ):
                            has_sender_eq_zero = True
                        elif (
                            isinstance(ir, SolidityCall)
                            and ir.function.name == "code(address)"
                            and (
                                SolidityVariableComposed("msg.sender") in ir.read
                                or SolidityVariableComposed("tx.origin") in ir.read
                            )
                        ):
                            ref_code_call = ir.lvalue
                        elif (
                            isinstance(ir, Member)
                            and ir.variable_right == "length"
                            and ir.variable_left == ref_code_call
                        ):
                            ref_length_access = ir.lvalue

                    if has_sender_eq_origin and not has_sender_eq_zero:
                        results.append(n)
    return results


class MsgSenderEqTxOrigin(AbstractDetector):
    """
    Detect the use of msg.sender checked against tx.origin.
    """

    ARGUMENT = "sender-eq-origin"
    HELP = "msg.sender checked against tx.origin"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#msg-sender-checked-against-tx-origin"

    WIKI_TITLE = "`msg.sender` checked against `tx.origin`"
    WIKI_DESCRIPTION = """
        Detect the use of `msg.sender` checked against `tx.origin`. 
        With [EIP-7702](https://eips.ethereum.org/EIPS/eip-7702) an EOA can have an associated code. 
        If the check is used to assume the caller is an EOA with no code it does not hold anymore and could be problematic.
    """
    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MsgSenderEqTxOrigin{
    function bad() public {
        if (msg.sender == tx.origin) {
            revert();
        }
    }
}
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = """
Design the contract such that other contracts can interacti with it without any potential issues or add an additional check on the msg.sender code length to be 0.
"""

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []
        for c in self.compilation_unit.contracts_derived:
            values = detect_sender_checked_origin(c)
            for node in values:
                func = node.function

                info: DETECTOR_INFO = [
                    func,
                    " checks msg.sender against tx.origin: ",
                    node,
                    "\n",
                ]

                res = self.generate_result(info)
                results.append(res)

        return results
