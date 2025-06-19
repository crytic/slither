""" "
Re-entrancy detection
"""

from collections import namedtuple, defaultdict
from typing import List, Dict, Set
from slither.core.declarations.function import Function
from slither.core.variables.state_variable import StateVariable
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
from slither.slithir.operations import Send, Transfer


FindingKey = namedtuple("FindingKey", ["function", "calls", "send_eth"])
FindingValue = namedtuple("FindingValue", ["variable", "node", "nodes", "cross_functions"])


class ReentrancyEthDF(AbstractDetector):
    ARGUMENT = "reentrancy-eth-df"
    HELP = "Reentrancy vulnerabilities (theft of ethers)"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities"
    )

    WIKI_TITLE = "Reentrancy vulnerabilities"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detection of the [reentrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Do not report reentrancies that don't involve Ether (see `reentrancy-no-eth`)"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    function withdrawBalance(){
        // send userBalance[msg.sender] Ether to msg.sender
        // if msg.sender is a contract, it will call its fallback function
        if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
            throw;
        }
        userBalance[msg.sender] = 0;
    }
```

Bob uses the re-entrancy bug to call `withdrawBalance` two times, and withdraw more than its initial deposit to the contract."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Apply the [`check-effects-interactions pattern`](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy)."

    STANDARD_JSON = False

    def find_reentrancies(self) -> Dict[FindingKey, Set[FindingValue]]:
        """
        Per-function reentrancy detection that handles modifiers correctly.
        """
        result: Dict[FindingKey, Set[FindingValue]] = defaultdict(set)

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

                    for call_node, call_destinations in state.calls.items():
                        if call_node not in function_calls:
                            function_calls[call_node] = set()
                        function_calls[call_node].update(call_destinations)

                    # ONLY track unsafe ETH calls for reentrancy detection
                    for send_node, send_destinations in state.send_eth.items():
                        if send_node not in function_send_eth:
                            function_send_eth[send_node] = set()
                        function_send_eth[send_node].update(send_destinations)

                    if not state.send_eth:
                        continue

                    processed_vars = set()

                    for eth_call_node in state.send_eth.keys():

                        vars_read_before_call = state.reads_prior_calls.get(eth_call_node, set())

                        if not vars_read_before_call:
                            continue

                        for var in vars_read_before_call:
                            if not isinstance(var, StateVariable):
                                continue

                            if var in processed_vars:
                                continue

                            # Use the contract-level reentrancy info (cross-function context)
                            if var not in variables_used_in_reentrancy:
                                continue

                            writing_nodes = state.written.get(var, set())
                            if not writing_nodes:
                                continue

                            # Check if current node writes this variable
                            if var in node.state_variables_written:
                                # Check if write could happen after ETH call
                                could_be_post_call_write = any(
                                    self._could_execute_after_call(eth_call_node, node)
                                    for eth_call_node in state.send_eth.keys()
                                    if var in state.reads_prior_calls.get(eth_call_node, set())
                                )

                                if could_be_post_call_write:
                                    processed_vars.add(var)

                                    cross_functions = variables_used_in_reentrancy.get(var, [])
                                    if isinstance(cross_functions, set):
                                        cross_functions = list(cross_functions)

                                    finding_value = FindingValue(
                                        var,
                                        node,
                                        tuple(sorted(writing_nodes, key=lambda x: x.node_id)),
                                        tuple(sorted(cross_functions, key=lambda x: str(x))),
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

    def _could_execute_after_call(self, call_node: Node, write_node: Node) -> bool:
        if call_node.function != write_node.function:
            return False

        def is_reachable(from_node: Node, to_node: Node, visited: set) -> bool:
            if from_node == to_node:
                return True
            if from_node in visited:
                return False
            visited.add(from_node)
            return any(is_reachable(son, to_node, visited.copy()) for son in from_node.sons)

        result = is_reachable(call_node, write_node, set())

        return result

    def _detect(self):  # pylint: disable=too-many-branches,too-many-locals
        """"""
        super()._detect()

        reentrancies = self.find_reentrancies()

        results = []

        result_sorted = sorted(list(reentrancies.items()), key=lambda x: x[0].function.name)
        varsWritten: List[FindingValue]
        varsWrittenSet: Set[FindingValue]
        for (func, calls, send_eth), varsWrittenSet in result_sorted:
            calls = sorted(list(set(calls)), key=lambda x: x[0].node_id)
            send_eth = sorted(list(set(send_eth)), key=lambda x: x[0].node_id)
            varsWritten = sorted(varsWrittenSet, key=lambda x: (x.variable.name, x.node.node_id))

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
            info += ["\tState variables written after the call(s):\n"]
            for finding_value in varsWritten:
                info += ["\t- ", finding_value.node, "\n"]
                for other_node in finding_value.nodes:
                    if other_node != finding_value.node:
                        info += ["\t\t- ", other_node, "\n"]
                if finding_value.cross_functions:
                    info += [
                        "\t",
                        finding_value.variable,
                        " can be used in cross function reentrancies:\n",
                    ]
                    for cross in finding_value.cross_functions:
                        info += ["\t- ", cross, "\n"]

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

            # Add all variables written via nodes which write them.
            for finding_value in varsWritten:
                res.add(
                    finding_value.node,
                    {
                        "underlying_type": "variables_written",
                        "variable_name": finding_value.variable.name,
                    },
                )
                for other_node in finding_value.nodes:
                    if other_node != finding_value.node:
                        res.add(
                            other_node,
                            {
                                "underlying_type": "variables_written",
                                "variable_name": finding_value.variable.name,
                            },
                        )

            # Append our result
            results.append(res)

        return results
