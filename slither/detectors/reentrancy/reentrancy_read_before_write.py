""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""

from slither.detectors.abstract_detector import DetectorClassification


from .reentrancy import Reentrancy

class ReentrancyReadBeforeWritten(Reentrancy):
    ARGUMENT = 'reentrancy-no-eth'
    HELP = 'Reentrancy vulnerabilities (no theft of ethers)'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-1'

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

    STANDARD_JSON = False

    def find_reentrancies(self):
        result = {}
        for contract in self.contracts:
            for f in contract.functions_and_modifiers_declared:
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

            info = ['Reentrancy in ', func, ':\n']

            info += ['\tExternal calls:\n']
            for call_info in calls:
                info += ['\t- ', call_info, '\n']
            info += '\tState variables written after the call(s):\n'
            for (v, node) in sorted(varsWritten, key=lambda x: (x[0].name, x[1].node_id)):
                info += ['\t- ', v, ' in ', node, '\n']

            # Create our JSON result
            json = self.generate_json_result(info)

            # Add the function with the re-entrancy first
            self.add_function_to_json(func, json)

            # Add all underlying calls in the function which are potentially problematic.
            for call_info in calls:
                self.add_node_to_json(call_info, json, {
                    "underlying_type": "external_calls"
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
