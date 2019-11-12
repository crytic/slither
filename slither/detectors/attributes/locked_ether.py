"""
    Check if ethers are locked in the contract
"""

from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, LowLevelCall, Send,
                                        Transfer, NewContract, LibraryCall, InternalCall)


class LockedEther(AbstractDetector):
    """
    """

    ARGUMENT = 'locked-ether'
    HELP = "Contracts that lock ether"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#contracts-that-lock-ether'


    WIKI_TITLE = 'Contracts that lock ether'
    WIKI_DESCRIPTION = 'Contract with a `payable` function, but without a withdraw capacity.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
pragma solidity 0.4.24;
contract Locked{
    function receive() payable public{
    }
}
```
Every ether sent to `Locked` will be lost.'''

    WIKI_RECOMMENDATION = 'Remove the payable attribute or add a withdraw function.'

    @staticmethod
    def do_no_send_ether(contract):
        functions = contract.all_functions_called
        to_explore = functions
        explored = []
        while to_explore:
            functions = to_explore
            explored += to_explore
            to_explore = []
            for function in functions:
                calls = [c.name for c in function.internal_calls]
                if 'suicide(address)' in calls or 'selfdestruct(address)' in calls:
                    return False
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, (Send, Transfer, HighLevelCall, LowLevelCall, NewContract)):
                            if ir.call_value and ir.call_value != 0:
                                return False
                        if isinstance(ir, (LowLevelCall)):
                            if ir.function_name in ['delegatecall', 'callcode']:
                                return False
                        # If a new internal call or librarycall
                        # Add it to the list to explore
                        # InternalCall if to follow internal call in libraries
                        if isinstance(ir, (InternalCall, LibraryCall)):
                            if not ir.function in explored:
                                to_explore.append(ir.function)

        return True


    def _detect(self):
        results = []

        for contract in self.slither.contracts_derived:
            if contract.is_signature_only():
                continue
            funcs_payable = [function for function in contract.functions if function.payable]
            if funcs_payable:
                if self.do_no_send_ether(contract):
                    info = [f"Contract locking ether found in {self.filename}:\n"]
                    info += ["\tContract ", contract, " has payable functions:\n"]
                    for function in funcs_payable:
                        info += [f"\t - ", function, "\n"]
                    info += "\tBut does not have a function to withdraw the ether\n"

                    json = self.generate_result(info)

                    results.append(json)

        return results
