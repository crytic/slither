""" "
Re-entrancy detection (No ETH)
"""

from collections import defaultdict, namedtuple
from typing import Dict, List, Set

from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.reentrancy import (DomainVariant,
                                                   ReentrancyAnalysis,
                                                   ReentrancyDomain)
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import (AbstractDetector,
                                                 DetectorClassification)
from slither.detectors.reentrancy.reentrancy import to_hashable
from slither.slithir.operations import Send, Transfer
from slither.utils.output import Output

FindingKey = namedtuple("FindingKey", ["function", "calls"])
FindingValue = namedtuple("FindingValue", ["variable", "node", "nodes", "cross_functions"])


class ReentrancyNoEthDF(AbstractDetector):
    ARGUMENT = "reentrancy-no-eth-df"
    HELP = "Reentrancy vulnerabilities (no theft of ethers)"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-1"
    )

    WIKI_TITLE = "Reentrancy vulnerabilities"

    # region wiki_description
    WIKI_DESCRIPTION = """
Detection of the [reentrancy bug](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy).
Do not report reentrancies that involve Ether (see `reentrancy-eth`)"""
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    function bug(){
        require(not_called);
        if( ! (msg.sender.call() ) ){
            throw;
        }
        not_called = False;
    }
```

The function `bug` has a reentrancy bug, it can be called multiple times and is not protected by a mutex."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Apply the [`check-effects-interactions pattern`](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy)."

    STANDARD_JSON = False

    def find_reentrancies(self) -> Dict[FindingKey, Set[FindingValue]]:
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

                    # Track unsafe ETH calls for exclusion
                    for send_node, send_destinations in state.send_eth.items():
                        if send_node not in function_send_eth:
                            function_send_eth[send_node] = set()
                        function_send_eth[send_node].update(send_destinations)

                    if not state.calls:
                        continue

                    if state.send_eth or state.safe_send_eth:
                        continue

                    processed_vars = set()

                    for call_node in state.calls.keys():

                        if call_node in state.send_eth:
                            continue

                        vars_read_before_call = state.reads_prior_calls.get(call_node, set())

                        if not vars_read_before_call:
                            continue

                        for var in vars_read_before_call:
                            # Find the actual StateVariable by canonical name
                            state_var = None
                            for sv in contract.state_variables:
                                if sv.canonical_name == var:
                                    state_var = sv
                                    break

                            if not state_var or not isinstance(state_var, StateVariable):
                                continue

                            if state_var in processed_vars:
                                continue

                            # Use the contract-level reentrancy info (cross-function context)
                            if state_var not in variables_used_in_reentrancy:
                                continue

                            writing_nodes = state.written.get(var, set())
                            if not writing_nodes:
                                continue

                            if state_var in node.state_variables_written:
                                could_be_post_call_write = self._could_execute_after_call(
                                    call_node, node
                                )

                                if could_be_post_call_write:
                                    processed_vars.add(state_var)

                                    cross_functions = variables_used_in_reentrancy.get(
                                        state_var, []
                                    )
                                    if isinstance(cross_functions, set):
                                        cross_functions = list(cross_functions)

                                    finding_value = FindingValue(
                                        state_var,
                                        node,
                                        tuple(sorted(writing_nodes, key=lambda x: x.node_id)),
                                        tuple(sorted(cross_functions, key=lambda x: str(x))),
                                    )
                                    vulnerable_findings.add(finding_value)

                if vulnerable_findings:
                    finding_key = FindingKey(
                        function=f,
                        calls=to_hashable(function_calls),
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

    def _detect(self) -> List[Output]:  # pylint: disable=too-many-branches
        """"""

        super()._detect()
        reentrancies = self.find_reentrancies()

        results = []

        result_sorted = sorted(list(reentrancies.items()), key=lambda x: x[0].function.name)
        varsWritten: List[FindingValue]
        varsWrittenSet: Set[FindingValue]
        for (func, calls), varsWrittenSet in result_sorted:
            calls = sorted(list(set(calls)), key=lambda x: x[0].node_id)
            varsWritten = sorted(varsWrittenSet, key=lambda x: (x.variable.name, x.node.node_id))

            info = ["Reentrancy in ", func, ":\n"]

            info += ["\tExternal calls:\n"]
            for call_info, calls_list in calls:
                info += ["\t- ", call_info, "\n"]
                for call_list_info in calls_list:
                    if call_list_info != call_info:
                        info += ["\t\t- ", call_list_info, "\n"]
            info += "\tState variables written after the call(s):\n"
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
