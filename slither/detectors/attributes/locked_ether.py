"""
    Check if ether are locked in the contract
"""

from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.slithir.operations import (HighLevelCall, LowLevelCall, Send,
                                        Transfer)


class LockedEther(AbstractDetector):
    """
    """

    ARGUMENT = 'locked-ether'
    HELP = "Contracts that lock ether"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    @staticmethod
    def do_no_send_ether(contract):
        functions = contract.all_functions_called
        for function in functions:
            calls = [c.name for c in function.internal_calls]
            if 'suicide(address)' in calls or 'selfdestruct(address)' in calls:
                return False
            for node in function.nodes:
                for ir in node.irs:
                    if isinstance(ir, (Send, Transfer, HighLevelCall, LowLevelCall)):
                        if ir.call_value and ir.call_value != 0:
                            return False
                    if isinstance(ir, (LowLevelCall)):
                        if ir.function_name in ['delegatecall', 'callcode']:
                            return False
        return True


    def detect(self):
        results = []

        for contract in self.slither.contracts_derived:
            if contract.is_signature_only():
                continue
            funcs_payable = [function for function in contract.functions if function.payable]
            if funcs_payable:
                if self.do_no_send_ether(contract):
                    txt = "Contract locked ether in {}, Contract {}, Functions {}"
                    info = txt.format(self.filename,
                                      contract.name,
                                      [f.name for f in funcs_payable])
                    self.log(info)

                    source = [f.source_mapping for f in funcs_payable]

                    results.append({'vuln': 'LockedEther',
                                    'functions_payable' : [f.name for f in funcs_payable],
                                    'contract': contract.name,
                                    'sourceMapping': source})

        return results
