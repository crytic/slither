""" "
Reentrancy Events detection

Detect when an event is emitted after an external call leading to out-of-order events
"""

from collections import namedtuple, defaultdict
from typing import DefaultDict, List, Set
from slither.core.declarations.function import Function
from slither.core.cfg.node import Node
from slither.detectors.abstract_detector import DetectorClassification

from slither.analyses.data_flow.reentrancy import (
    DomainVariant,
    ReentrancyAnalysis,
    ReentrancyDomain,
)
from slither.analyses.data_flow.engine import Engine
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.detectors.reentrancy.reentrancy import to_hashable
from slither.utils.output import Output
from slither.slithir.operations import EventCall


FindingKey = namedtuple("FindingKey", ["function", "calls", "send_eth"])
FindingValue = namedtuple("FindingValue", ["variable", "node", "nodes"])


class ReentrancyEventDF(AbstractDetector):
    ARGUMENT = "reentrancy-events-df"
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
        """
        Per-function reentrancy detection for events after external calls.
        Following the Rust implementation logic.
        """
        result = defaultdict(set)

        for contract in self.contracts:
            variables_used_in_reentrancy = contract.state_variables_used_in_reentrant_targets
            # Get all implemented functions for this contract
            functions = [
                f
                for f in contract.functions_and_modifiers_declared
                if f.is_implemented and not f.is_constructor
            ]
            for f in functions:
                engine = Engine.new(analysis=ReentrancyAnalysis(), functions=[f])
                engine.run_analysis()
                engine_result = engine.result()
                vulnerable_findings = set()
                function_calls = {}
                function_send_eth = {}

                for node in f.nodes:
                    if node not in engine_result:
                        continue

                    analysis = engine_result[node]
                    if not hasattr(analysis, "post") or not isinstance(
                        analysis.post, ReentrancyDomain
                    ):
                        continue

                    if analysis.post.variant != DomainVariant.STATE:
                        continue

                    state = analysis.post.state

                    # Collect external calls
                    for call_node, call_destinations in state.calls.items():
                        if call_node not in function_calls:
                            function_calls[call_node] = set()
                        function_calls[call_node].update(call_destinations)

                    # Collect ETH calls
                    for send_node, send_destinations in state.send_eth.items():
                        if send_node not in function_send_eth:
                            function_send_eth[send_node] = set()
                        function_send_eth[send_node].update(send_destinations)

                    # Following Rust logic: for each event, check if there are external calls
                    # BUT only if the event comes AFTER the call (execution order matters)
                    for event_call, event_nodes in state.events.items():
                        for call_node in state.calls.keys():
                            # Check if any event node can be reached from the call node
                            # (i.e., event executes after the call)
                            event_after_call = any(
                                self._could_execute_after_call(call_node, event_node)
                                for event_node in event_nodes
                            )

                            if event_after_call:
                                # Create a finding for this event-call combination
                                finding_value = FindingValue(
                                    event_call,
                                    list(event_nodes)[0] if event_nodes else node,
                                    tuple(sorted(event_nodes, key=lambda x: x.node_id)),
                                )
                                vulnerable_findings.add(finding_value)

                if vulnerable_findings:
                    finding_key = FindingKey(
                        function=f,
                        calls=to_hashable(function_calls),
                        send_eth=to_hashable(function_send_eth),
                    )
                    result[finding_key] |= vulnerable_findings

        return result

    def _could_execute_after_call(self, call_node: Node, event_node: Node) -> bool:
        """Check if an event node could execute after a call node"""
        if call_node.function != event_node.function:
            return False

        def is_reachable(from_node: Node, to_node: Node, visited: set) -> bool:
            if from_node == to_node:
                return True
            if from_node in visited:
                return False
            visited.add(from_node)
            return any(is_reachable(son, to_node, visited.copy()) for son in from_node.sons)

        return is_reachable(call_node, event_node, set())

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
            for call_info, calls_list in calls:
                info += ["\t- ", call_info, "\n"]
                for call_list_info in calls_list:
                    if call_list_info != call_info:
                        info += ["\t\t- ", call_list_info, "\n"]
            if calls != send_eth and send_eth:
                info += ["\tExternal calls sending eth:\n"]
                for call_info, calls_list in send_eth:
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
            for call_info, calls_list in calls:
                res.add(call_info, {"underlying_type": "external_calls"})
                for call_list_info in calls_list:
                    if call_list_info != call_info:
                        res.add(
                            call_list_info,
                            {"underlying_type": "external_calls_sending_eth"},
                        )

            # If the calls are not the same ones that send eth, add the eth sending nodes.
            if calls != send_eth:
                for call_info, calls_list in send_eth:
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
