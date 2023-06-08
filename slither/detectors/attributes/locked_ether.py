"""
    Check if ethers are locked in the contract
"""
from typing import List

from slither.core.declarations import Contract, SolidityFunction
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import (
    HighLevelCall,
    LowLevelCall,
    Send,
    Transfer,
    NewContract,
    LibraryCall,
    InternalCall,
    SolidityCall,
)
from slither.slithir.variables import Constant
from slither.utils.output import Output


class LockedEther(AbstractDetector):  # pylint: disable=too-many-nested-blocks

    ARGUMENT = "locked-ether"
    HELP = "Contracts that lock ether"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#contracts-that-lock-ether"

    WIKI_TITLE = "Contracts that lock Ether"
    WIKI_DESCRIPTION = "Contract with a `payable` function, but without a withdrawal capacity."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
pragma solidity 0.4.24;
contract Locked{
    function receive() payable public{
    }
}
```
Every Ether sent to `Locked` will be lost."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Remove the payable attribute or add a withdraw function."

    @staticmethod
    def do_no_send_ether(contract: Contract) -> bool:
        functions = contract.all_functions_called
        to_explore = functions
        explored = []
        while to_explore:  # pylint: disable=too-many-nested-blocks
            functions = to_explore
            explored += to_explore
            to_explore = []
            for function in functions:
                calls = [c.name for c in function.internal_calls]
                if "suicide(address)" in calls or "selfdestruct(address)" in calls:
                    return False
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(
                            ir,
                            (Send, Transfer, HighLevelCall, LowLevelCall, NewContract),
                        ):
                            if ir.call_value and ir.call_value != 0:
                                return False
                        if isinstance(ir, (LowLevelCall)) and ir.function_name in [
                            "delegatecall",
                            "callcode",
                        ]:
                            return False
                        if isinstance(ir, SolidityCall):
                            call_can_send_ether = ir.function in [
                                SolidityFunction(
                                    "delegatecall(uint256,uint256,uint256,uint256,uint256,uint256)"
                                ),
                                SolidityFunction(
                                    "callcode(uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
                                ),
                                SolidityFunction(
                                    "call(uint256,uint256,uint256,uint256,uint256,uint256,uint256)"
                                ),
                            ]
                            nonzero_call_value = call_can_send_ether and (
                                not isinstance(ir.arguments[2], Constant)
                                or ir.arguments[2].value != 0
                            )
                            if nonzero_call_value:
                                return False
                        # If a new internal call or librarycall
                        # Add it to the list to explore
                        # InternalCall if to follow internal call in libraries
                        if isinstance(ir, (InternalCall, LibraryCall)):
                            if not ir.function in explored:
                                to_explore.append(ir.function)

        return True

    def _detect(self) -> List[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            if contract.is_signature_only():
                continue
            funcs_payable = [function for function in contract.functions if function.payable]
            if funcs_payable:
                if self.do_no_send_ether(contract):
                    info: DETECTOR_INFO = ["Contract locking ether found:\n"]
                    info += ["\tContract ", contract, " has payable functions:\n"]
                    for function in funcs_payable:
                        info += ["\t - ", function, "\n"]
                    info += "\tBut does not have a function to withdraw the ether\n"

                    json = self.generate_result(info)

                    results.append(json)

        return results
