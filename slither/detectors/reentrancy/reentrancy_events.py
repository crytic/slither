""""
    Re-entrancy detection

    Based on heuristics, it may lead to FP and FN
    Iterate over all the nodes of the graph until reaching a fixpoint
"""
from collections import namedtuple, defaultdict
from typing import DefaultDict, List, Set

from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.reentrancy.reentrancy import Reentrancy, to_hashable
from slither.utils.output import Output

FindingKey = namedtuple("FindingKey", ["function", "calls", "send_eth"])
FindingValue = namedtuple("FindingValue", ["variable", "node", "nodes"])


class ReentrancyEvent(Reentrancy):
    ARGUMENT = "reentrancy-events"
    HELP = "Reentrancy vulnerabilities leading to out-of-order Events"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-3"
    )

    WIKI_TITLE = "Reentrancy vulnerabilities"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detects [reentrancies](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy) that allow manipulation of the order or value of events."""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract ReentrantContract {
	function f() external {
		if (BugReentrancyEvents(msg.sender).counter() == 1) {
			BugReentrancyEvents(msg.sender).count(this);
		}
	}
}
contract Counter {
	uint public counter;
	event Counter(uint);

}
contract BugReentrancyEvents is Counter {
    function count(ReentrantContract d) external {
        counter += 1;
        d.f();
        emit Counter(counter);
    }
}
contract NoReentrancyEvents is Counter {
	function count(ReentrantContract d) external {
        counter += 1;
        emit Counter(counter);
        d.f();
    }
}
```

If the external call `d.f()` re-enters `BugReentrancyEvents`, the `Counter` events will be incorrect (`Counter(2)`, `Counter(2)`) whereas `NoReentrancyEvents` will correctly emit 
(`Counter(1)`, `Counter(2)`). This may cause issues for offchain components that rely on the values of events e.g. checking for the amount deposited to a bridge."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Apply the [`check-effects-interactions` pattern](https://docs.soliditylang.org/en/latest/security-considerations.html#re-entrancy)."

    STANDARD_JSON = False

    def find_reentrancies(self) -> DefaultDict[FindingKey, Set[FindingValue]]:
        result = defaultdict(set)
        for contract in self.contracts:
            for f in contract.functions_and_modifiers_declared:
                if not f.is_reentrant:
                    continue
                for node in f.nodes:
                    # dead code
                    if self.KEY not in node.context:
                        continue
                    if node.context[self.KEY].calls:
                        if not any(n != node for n in node.context[self.KEY].calls):
                            continue

                        # calls are ordered
                        finding_key = FindingKey(
                            function=node.function,
                            calls=to_hashable(node.context[self.KEY].calls),
                            send_eth=to_hashable(node.context[self.KEY].send_eth),
                        )
                        finding_vars = {
                            FindingValue(
                                e,
                                e.node,
                                tuple(sorted(nodes, key=lambda x: x.node_id)),
                            )
                            for (e, nodes) in node.context[self.KEY].events.items()
                        }
                        if finding_vars:
                            result[finding_key] |= finding_vars
        return result

    def _detect(self) -> List[Output]:  # pylint: disable=too-many-branches
        """"""
        super()._detect()

        reentrancies = self.find_reentrancies()

        results = []

        result_sorted = sorted(list(reentrancies.items()), key=lambda x: x[0][0].name)
        for (func, calls, send_eth), events in result_sorted:
            calls = sorted(list(set(calls)), key=lambda x: x[0].node_id)
            send_eth = sorted(list(set(send_eth)), key=lambda x: x[0].node_id)
            events = sorted(events, key=lambda x: (str(x.variable.name), x.node.node_id))

            info = ["Reentrancy in ", func, ":\n"]
            info += ["\tExternal calls:\n"]
            for (call_info, calls_list) in calls:
                info += ["\t- ", call_info, "\n"]
                for call_list_info in calls_list:
                    if call_list_info != call_info:
                        info += ["\t\t- ", call_list_info, "\n"]
            if calls != send_eth and send_eth:
                info += ["\tExternal calls sending eth:\n"]
                for (call_info, calls_list) in send_eth:
                    info += ["\t- ", call_info, "\n"]
                    for call_list_info in calls_list:
                        if call_list_info != call_info:
                            info += ["\t\t- ", call_list_info, "\n"]
            info += ["\tEvent emitted after the call(s):\n"]
            for finding_value in events:
                info += ["\t- ", finding_value.node, "\n"]
                for other_node in finding_value.nodes:
                    if other_node != finding_value.node:
                        info += ["\t\t- ", other_node, "\n"]

            # Create our JSON result
            res = self.generate_result(info)

            # Add the function with the re-entrancy first
            res.add(func)

            # Add all underlying calls in the function which are potentially problematic.
            for (call_info, calls_list) in calls:
                res.add(call_info, {"underlying_type": "external_calls"})
                for call_list_info in calls_list:
                    if call_list_info != call_info:
                        res.add(
                            call_list_info,
                            {"underlying_type": "external_calls_sending_eth"},
                        )

            #

            # If the calls are not the same ones that send eth, add the eth sending nodes.
            if calls != send_eth:
                for (call_info, calls_list) in send_eth:
                    res.add(call_info, {"underlying_type": "external_calls_sending_eth"})
                    for call_list_info in calls_list:
                        if call_list_info != call_info:
                            res.add(
                                call_list_info,
                                {"underlying_type": "external_calls_sending_eth"},
                            )

            for finding_value in events:
                res.add(finding_value.node, {"underlying_type": "event"})
                for other_node in finding_value.nodes:
                    if other_node != finding_value.node:
                        res.add(other_node, {"underlying_type": "event"})

            # Append our result
            results.append(res)

        return results
