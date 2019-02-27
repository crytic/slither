""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""

from slither.core.cfg.node import NodeType
from slither.core.declarations import Function, SolidityFunction
from slither.core.expressions import UnaryOperation, UnaryOperationType
from slither.detectors.abstract_detector import DetectorClassification
from slither.visitors.expression.export_values import ExportValues
from slither.slithir.operations import (HighLevelCall, LowLevelCall,
                                        LibraryCall,
                                        Send, Transfer)


from .reentrancy import Reentrancy

class ReentrancyReadBeforeWritten(Reentrancy):
    ARGUMENT = 'reentrancy-no-eth'
    HELP = 'Reentrancy vulnerabilities (no theft of ethers)'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/trailofbits/slither/wiki/Detectors-Documentation#reentrancy-vulnerabilities-1'

    WIKI_TITLE = 'Reentrancy vulnerabilities'
    WIKI_DESCRIPTION = '''
Detection of the [re-entrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Do not report reentrancies that involve ethers (see `reentrancy-eth`)'''

    WIKI_EXPLOIT_SCENARIO = '''
```solidity
    function bug(){
        require(not_called);
        if( ! (msg.sender.call() ) ){
            throw;
        }
        not_called = False;
    }   
```
'''
    WIKI_RECOMMENDATION = 'Apply the [check-effects-interactions pattern](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy).'

    def find_reentrancies(self):
        result = {}
        for contract in self.contracts:
            for f in contract.functions_and_modifiers_not_inherited:
                for node in f.nodes:
                    # dead code
                    if not self.KEY in node.context:
                        continue
                    if node.context[self.KEY]['calls'] and not node.context[self.KEY]['send_eth']:
                        read_then_written = []
                        for c in node.context[self.KEY]['calls']:
                            if c == node:
                                continue
                            read_then_written += [(v, node) for v in node.context[self.KEY]['written']
                                                  if v in node.context[self.KEY]['read_prior_calls'][c]]

                        # We found a potential re-entrancy bug
                        if read_then_written:
                            # calls are ordered
                            finding_key = (node.function,
                                           tuple(sorted(list(node.context[self.KEY]['calls']), key=lambda x:x.node_id)))
                            finding_vars = read_then_written
                            if finding_key not in result:
                                result[finding_key] = []
                            result[finding_key] = list(set(result[finding_key] + finding_vars))
        return result

    def _detect(self):
        """
        """

        super()._detect()
        reentrancies = self.find_reentrancies()

        results = []

        result_sorted = sorted(list(reentrancies.items()), key=lambda x:x[0][0].name)
        for (func, calls), varsWritten in result_sorted:
            calls = sorted(list(set(calls)), key=lambda x: x.node_id)
            info = 'Reentrancy in {}.{} ({}):\n'
            info = info.format(func.contract.name, func.name, func.source_mapping_str)
            info += '\tExternal calls:\n'
            for call_info in calls:
                info += '\t- {} ({})\n'.format(call_info.expression, call_info.source_mapping_str)
            info += '\tState variables written after the call(s):\n'
            for (v, node) in sorted(varsWritten, key=lambda x: (x[0].name, x[1].node_id)):
                info +=  '\t- {} ({})\n'.format(v, node.source_mapping_str)

            sending_eth_json = []

            json = self.generate_json_result(info)
            self.add_function_to_json(func, json)
            json['elements'] += [{'type': 'external_calls',
                                  'expression': str(call_info.expression),
                                  'source_mapping': call_info.source_mapping}
                                 for call_info in calls]
            json['elements'] += sending_eth_json
            json['elements'] += [{'type':'variables_written',
                                   'name': v.name,
                                   'expression': str(node.expression),
                                   'source_mapping': node.source_mapping}
                                  for (v, node) in varsWritten]
            results.append(json)

        return results
