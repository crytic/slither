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

    WIKI = 'https://github.com/trailofbits/slither/wiki/Vulnerabilities-Description#controlled-delegatecall'


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
Bob calls `delegate` and delegate the execution to its malicious contract. As a result, Bob withdraws the funds of the contract and destruct it.'''

    WIKI_RECOMMENDATION = 'Avoid using `delegatecall`. Use only trusted destinations.'

    def controlled_delegatecall(self, function):
        ret = []
        for node in function.nodes:
            for ir in node.irs:
                if isinstance(ir, LowLevelCall) and ir.function_name in ['delegatecall', 'codecall']:
                    if is_tainted(ir.destination, function.contract):
                        ret.append(node)
        return ret

    def _detect(self):
        results = []

        for contract in self.slither.contracts:
            for f in contract.functions:
                if f.contract != contract:
                    continue
                nodes = self.controlled_delegatecall(f)
                if nodes:
                    info = '{}.{} ({}) uses delegatecall to a input-controlled function id\n'
                    info = info.format(contract.name, f.name, f.source_mapping_str)
                    for node in nodes:
                        info += '\t{} ({})\n'.format(node.expression, node.source_mapping_str)

                    json = self.generate_json_result(info)
                    self.add_function_to_json(f, json)
                    self.add_nodes_to_json(nodes, json)
                    results.append(json)

        return results
