from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import LowLevelCall
from slither.analyses.data_dependency.data_dependency import is_tainted


class ControlledDelegateCall(AbstractDetector):
    """
    """

    ARGUMENT = 'controlled-delegatecall'
    HELP = 'Controlled delegatecall destination'
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#controlled-delegatecall'


    WIKI_TITLE = 'Controlled Delegatecall'
    WIKI_DESCRIPTION = 'Delegatecall or callcode to an address controlled by the user.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract Delegatecall{
    function delegate(address to, bytes data){
        to.delegatecall(data);
    }
}
```
Bob calls `delegate` and delegates the execution to its malicious contract. As a result, Bob withdraws the funds of the contract and destructs it.'''

    WIKI_RECOMMENDATION = 'Avoid using `delegatecall`. Use only trusted destinations.'

    def controlled_delegatecall(self, function):
        ret = []
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, LowLevelCall) and ir.function_name in ['delegatecall', 'callcode']:
                    if is_tainted(ir.destination, function.contract):
                        ret.append(node)
        return ret

    def _detect(self):
        results = []

        for contract in self.slither.contracts:
            for f in contract.functions:
                if f.contract_declarer != contract:
                    continue
                nodes = self.controlled_delegatecall(f)
                if nodes:
                    func_info = [f, ' uses delegatecall to a input-controlled function id\n']

                    for node in nodes:
                        node_info = func_info + ['\t- ', node,'\n']
                        res = self.generate_result(node_info)
                        results.append(res)

        return results
