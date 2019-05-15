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

class ReentrancyBenign(Reentrancy):
    ARGUMENT = 'reentrancy-benign'
    HELP = 'Benign reentrancy vulnerabilities'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-2'

    WIKI_TITLE = 'Reentrancy vulnerabilities'
    WIKI_DESCRIPTION = '''
Detection of the [re-entrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Only report reentrancy that acts as a double call (see `reentrancy-eth`, `reentrancy-no-eth`).'''
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
    function callme(){
        if( ! (msg.sender.call()() ) ){
            throw;
        }
        counter += 1
    }   
```

`callme` contains a reentrancy. The reentrancy is benign because it's exploitation would have the same effect as two consecutive calls.'''

    WIKI_RECOMMENDATION = 'Apply the [check-effects-interactions pattern](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy).'

    def find_reentrancies(self):
        result = {}
        for contract in self.contracts:
            for f in contract.functions_and_modifiers_declared:
                for node in f.nodes:
                    # dead code
                    if not self.KEY in node.context:
                        continue
                    if node.context[self.KEY]['calls']:
                        if not any(n!=node for n in node.context[self.KEY]['calls']):
                            continue
                        read_then_written = []
                        for c in node.context[self.KEY]['calls']:
                            read_then_written += [v for v in node.context[self.KEY]['written']
                                                 if v in node.context[self.KEY]['read_prior_calls'][c]]
                        not_read_then_written = [(v, node) for v in node.context[self.KEY]['written']
                                                 if v not in read_then_written]
                        if not_read_then_written:

                            # calls are ordered
                            finding_key = (node.function,
                                           tuple(sorted(list(node.context[self.KEY]['calls']), key=lambda x:x.node_id)),
                                           tuple(sorted(list(node.context[self.KEY]['send_eth']), key=lambda x:x.node_id)))
                            finding_vars = not_read_then_written
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
        for (func, calls, send_eth), varsWritten in result_sorted:
            calls = sorted(list(set(calls)), key=lambda x: x.node_id)
            send_eth = sorted(list(set(send_eth)), key=lambda x: x.node_id)
            info = 'Reentrancy in {} ({}):\n'
            info = info.format(func.canonical_name, func.source_mapping_str)
            info += '\tExternal calls:\n'
            for call_info in calls:
                info += '\t- {} ({})\n'.format(call_info.expression, call_info.source_mapping_str)
            if calls != send_eth and send_eth:
                info += '\tExternal calls sending eth:\n'
                for call_info in send_eth:
                    info += '\t- {} ({})\n'.format(call_info.expression, call_info.source_mapping_str)
            info += '\tState variables written after the call(s):\n'
            for (v, node) in sorted(varsWritten, key=lambda x: (x[0].name, x[1].node_id)):
                info += '\t- {} ({})\n'.format(v, node.source_mapping_str)

            # Create our JSON result
            json = self.generate_json_result(info)

            # Add the function with the re-entrancy first
            self.add_function_to_json(func, json)

            # Add all underlying calls in the function which are potentially problematic.
            for call_info in calls:
                self.add_node_to_json(call_info, json, {
                    "underlying_type": "external_calls"
                })

            #

            # If the calls are not the same ones that send eth, add the eth sending nodes.
            if calls != send_eth:
                for call_info in send_eth:
                    self.add_node_to_json(call_info, json, {
                        "underlying_type": "external_calls_sending_eth"
                    })

            # Add all variables written via nodes which write them.
            for (v, node) in varsWritten:
                self.add_node_to_json(node, json, {
                    "underlying_type": "variables_written",
                    "variable_name": v.name
                })

            # Append our result
            results.append(json)

        return results
