"""
Re-entrancy detection
"""

from collections import defaultdict, namedtuple
from typing import Dict, List, Set
from loguru import logger

from slither.analyses.data_flow.analyses.reentrancy.analysis.analysis import ReentrancyAnalysis
from slither.analyses.data_flow.analyses.reentrancy.analysis.domain import (
    DomainVariant,
    ReentrancyDomain,
)
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.variables.state_variable import StateVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.detectors.reentrancy.reentrancy import to_hashable
from slither.utils.output import Output

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
    Do not report reentrancies that don't involve Ether (see reentrancy-no-eth)
    """
    # endregion wiki_description

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
    solidity
        function withdrawBalance(){
            // send userBalance[msg.sender] Ether to msg.sender
            // if msg.sender is a contract, it will call its fallback function
            if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
                throw;
            }
            userBalance[msg.sender] = 0;
        }
    Bob uses the re-entrancy bug to call withdrawBalance two times, and withdraw more than its initial deposit to the contract.
    """
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Apply the [check-effects-interactions pattern](http://solidity.readthedocs.io/en/v0.4.21/security-considerations.html#re-entrancy)."
    STANDARD_JSON = False

    def find_reentrancies(self) -> Dict[FindingKey, Set[FindingValue]]:
        """Detect per-function reentrancy vulnerabilities using data flow analysis."""
        result: Dict[FindingKey, Set[FindingValue]] = defaultdict(set)

        for contract in self.contracts:
            variables_used_in_reentrancy = contract.state_variables_used_in_reentrant_targets
            functions = [
                f
                for f in contract.functions_and_modifiers_declared
                if f.is_implemented and not f.is_constructor
            ]

            for f in functions:
                engine = Engine.new(analysis=ReentrancyAnalysis(), functions=[f])
                engine.run_analysis()
                engine_result = engine.result()
                vulnerable_findings: Set[FindingValue] = set()
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

                    # Track calls and sends
                    for call_node, call_destinations in state.calls.items():
                        function_calls.setdefault(call_node, set()).update(call_destinations)
                    for send_node, send_destinations in state.send_eth.items():
                        function_send_eth.setdefault(send_node, set()).update(send_destinations)

                    # Skip if not all reentrancy conditions are met: ETH calls, state writes, and reads before calls
                    if not (
                        (state.send_eth or state.safe_send_eth)
                        and state.written
                        and state.reads_prior_calls
                    ):
                        continue

                    # Iterate through all calls that have variables read before them
                    for call_node, vars_read_before_call in state.reads_prior_calls.items():
                        # Check each variable that was read before a call
                        for var_canonical_name in vars_read_before_call:
                            # Find the actual StateVariable object by canonical name
                            var = next(
                                (
                                    sv
                                    for sv in contract.state_variables
                                    if sv.canonical_name == var_canonical_name
                                ),
                                None,
                            )
                            # Skip if variable not found or not a StateVariable
                            if not var or not isinstance(var, StateVariable):
                                continue

                            # Only proceed if this variable is written somewhere
                            if var_canonical_name not in state.written:
                                continue

                            writing_nodes = state.written[var_canonical_name]

                            # Filter out entry point nodes to avoid false positives
                            non_entry_writing_nodes = {
                                n for n in writing_nodes if n != f.entry_point
                            }

                            # Skip if no non-entry writing nodes found
                            if not non_entry_writing_nodes:
                                continue

                            # Only report if function is reentrant or variable used in cross-function reentrancy
                            if not (f.is_reentrant or var in variables_used_in_reentrancy):
                                continue

                            cross_functions = variables_used_in_reentrancy.get(var, [])

                            # Convert set to list if needed for consistent handling
                            if isinstance(cross_functions, set):
                                cross_functions = list(cross_functions)

                            # Use the first writing node as the main node for reporting
                            main_node = min(non_entry_writing_nodes, key=lambda x: x.node_id)

                            # Create finding value with all relevant information
                            finding_value = FindingValue(
                                var,
                                main_node,
                                tuple(sorted(non_entry_writing_nodes, key=lambda x: x.node_id)),
                                tuple(sorted(cross_functions, key=lambda x: str(x))),
                            )

                            # Add to vulnerable findings set
                            vulnerable_findings.add(finding_value)

                if vulnerable_findings:
                    finding_key = FindingKey(
                        function=f,
                        calls=to_hashable(function_calls),
                        send_eth=to_hashable(function_send_eth),
                    )
                    result[finding_key] |= vulnerable_findings

        return result

    def _detect(self) -> List[Output]:
        super()._detect()
        reentrancies = self.find_reentrancies()
        results = []

        result_sorted = sorted(list(reentrancies.items()), key=lambda x: x[0].function.name)

        for (func, calls, send_eth), varsWrittenSet in result_sorted:
            calls_dict = {
                call_node.node_id: (call_node, call_list) for call_node, call_list in calls
            }
            calls_sorted = sorted(calls_dict.values(), key=lambda x: x[0].node_id)
            send_eth_dict = {
                send_node.node_id: (send_node, send_list) for send_node, send_list in send_eth
            }
            send_eth_sorted = sorted(send_eth_dict.values(), key=lambda x: x[0].node_id)
            varsWritten = sorted(varsWrittenSet, key=lambda x: (x.variable.name, x.node.node_id))

            info = ["Reentrancy in ", func, ":\n"]
            info += ["\tExternal calls:\n"]
            for call_node, calls_list in calls_sorted:
                info += ["\t- ", call_node, "\n"]
                for c in calls_list:
                    if c != call_node:
                        info += ["\t\t- ", c, "\n"]

            calls_node_ids = {call_node.node_id for call_node, _ in calls_sorted}
            send_eth_node_ids = {send_node.node_id for send_node, _ in send_eth_sorted}
            if calls_node_ids != send_eth_node_ids and send_eth_sorted:
                info += ["\tExternal calls sending eth:\n"]
                for send_node, send_list in send_eth_sorted:
                    info += ["\t- ", send_node, "\n"]
                    for s in send_list:
                        if s != send_node:
                            info += ["\t\t- ", s, "\n"]

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

            res = self.generate_result(info)
            res.add(func)
            for call_node, calls_list in calls_sorted:
                res.add(call_node, {"underlying_type": "external_calls"})
                for c in calls_list:
                    if c != call_node:
                        res.add(c, {"underlying_type": "external_calls_sending_eth"})

            if calls_node_ids != send_eth_node_ids:
                for send_node, send_list in send_eth_sorted:
                    res.add(send_node, {"underlying_type": "external_calls_sending_eth"})
                    for s in send_list:
                        if s != send_node:
                            res.add(s, {"underlying_type": "external_calls_sending_eth"})

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
            results.append(res)

        return results
