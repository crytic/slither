""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""
from slither.detectors.abstract_detector import DetectorClassification

from .reentrancy import Reentrancy


class ReentrancyEvent(Reentrancy):
    ARGUMENT = 'reentrancy-events'
    HELP = 'Reentrancy vulnerabilities leading to out-of-order Events'
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-3'

    WIKI_TITLE = 'Reentrancy vulnerabilities'
    WIKI_DESCRIPTION = '''
Detection of the [re-entrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Only report reentrancies leading to out-of-order Events'''
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
    function bug(Called d){
        counter += 1;
        d.f();
        emit Counter(counter);
    }
```

If `d.()` reenters, the `Counter` events will be showed in an incorrect order, which might lead to issues for third-parties.'''

    WIKI_RECOMMENDATION = 'Apply the [check-effects-interactions pattern](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy).'

    STANDARD_JSON = False

    def find_reentrancies(self):
        result = {}
        for contract in self.contracts:
            for f in contract.functions_and_modifiers_declared:
                for node in f.nodes:
                    # dead code
                    if self.KEY not in node.context:
                        continue
                    if node.context[self.KEY].calls:
                        if not any(n != node for n in node.context[self.KEY].calls):
                            continue

                        # calls are ordered
                        finding_key = (node.function,
                                       tuple(sorted(list(node.context[self.KEY].calls), key=lambda x: x.node_id)),
                                       tuple(sorted(list(node.context[self.KEY].send_eth), key=lambda x: x.node_id)))
                        finding_vars = list(node.context[self.KEY].events)
                        if finding_vars:
                            if finding_key not in result:
                                result[finding_key] = set()
                            result[finding_key] = set(result[finding_key] | set(finding_vars))
        return result

    def _detect(self):
        """
        """
        super()._detect()

        reentrancies = self.find_reentrancies()

        results = []

        result_sorted = sorted(list(reentrancies.items()), key=lambda x: x[0][0].name)
        for (func, calls, send_eth), events in result_sorted:
            calls = sorted(list(set(calls)), key=lambda x: x.node_id)
            send_eth = sorted(list(set(send_eth)), key=lambda x: x.node_id)

            info = ['Reentrancy in ', func, ':\n']
            info += ['\tExternal calls:\n']
            for call_info in calls:
                info += ['\t- ', call_info, '\n']
            if calls != send_eth and send_eth:
                info += ['\tExternal calls sending eth:\n']
                for call_info in send_eth:
                    info += ['\t- ', call_info, '\n']
            info += ['\tEvent emitted after the call(s):\n']
            for event in sorted(events, key=lambda x: x.node.node_id):
                info += ['\t- ', event.node, '\n']

            # Create our JSON result
            res = self.generate_result(info)

            # Add the function with the re-entrancy first
            res.add(func)

            # Add all underlying calls in the function which are potentially problematic.
            for call_info in calls:
                res.add(call_info, {
                    "underlying_type": "external_calls"
                })

            #

            # If the calls are not the same ones that send eth, add the eth sending nodes.
            if calls != send_eth:
                for call_info in send_eth:
                    res.add(call_info, {
                        "underlying_type": "external_calls_sending_eth"
                    })

            # Append our result
            results.append(res)

        return results
