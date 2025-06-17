"""
Re-entrancy detection for ETH-sending calls using data flow analysis

Based on data flow analysis to detect reentrancy vulnerabilities
that specifically involve sending ETH
"""

from collections import defaultdict
from typing import Dict, List, NamedTuple, Set

from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.reentrancy import (
    DomainVariant,
    ReentrancyAnalysis,
    ReentrancyDomain,
)
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import HighLevelCall, InternalCall, LowLevelCall, Send, Transfer
from slither.slithir.operations.operation import Operation
from slither.utils.output import Output


class ReentrancyFinding(NamedTuple):
    """Represents a reentrancy vulnerability finding"""

    function: Function  # Function with reentrancy
    external_calls: Set[Node]  # External calls that can reenter
    variables_written: Dict[
        Variable, Set[Node]
    ]  # Variables written after external calls and their write locations
    internal_calls: Dict[
        Node, Set[Node]
    ]  # Internal calls that lead to reentrancy, mapped to their external call targets
    internal_variables_written: Dict[
        Node, Dict[Variable, Set[Node]]
    ]  # Variables written in internal calls, mapped by internal call node


class ReentrancyEthDF(AbstractDetector):
    """
    Reentrancy detector for ETH-sending calls using data flow analysis
    """

    ARGUMENT = "reentrancy-eth-df"
    HELP = "Reentrancy vulnerabilities in ETH-sending calls (data flow analysis)"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities"
    )

    WIKI_TITLE = "Reentrancy vulnerabilities (ETH sending)"

    WIKI_DESCRIPTION = """
Detects [reentrancies](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy) that involve sending ETH and can lead to loss of funds using data flow analysis."""

    WIKI_EXPLOIT_SCENARIO = """
```solidity
function withdraw(uint amount) public {
    require(balances[msg.sender] >= amount);
    msg.sender.call{value: amount}("");  // ETH send - vulnerable to reentrancy
    balances[msg.sender] -= amount;      // State change after external call
}
```
An attacker can reenter the function before the balance is updated, allowing multiple withdrawals."""

    WIKI_RECOMMENDATION = "Apply the [`check-effects-interactions` pattern](https://docs.soliditylang.org/en/latest/security-considerations.html#re-entrancy). Update state variables before making external calls that send ETH."

    STANDARD_JSON = False

    def __init__(self, compilation_unit, slither_instance, logger_obj):
        super().__init__(compilation_unit, slither_instance, logger_obj)
        self.analysis = ReentrancyAnalysis()

    def _send_eth(self, operation: Operation) -> bool:
        """Check if an operation sends ETH"""
        if isinstance(operation, (Send, Transfer)):
            return True
        elif isinstance(operation, (HighLevelCall, LowLevelCall)):
            return operation.call_value is not None and operation.call_value != 0
        return False

    def find_reentrancies(self) -> List[ReentrancyFinding]:
        findings = []

        functions = [f for c in self.contracts for f in c.functions if not f.is_constructor]

        for function in functions:
            # Run reentrancy analysis
            engine = Engine.new(analysis=ReentrancyAnalysis(), functions=[function])
            engine.run_analysis()
            results = engine.result()

            for _, analysis in results.items():
                if not hasattr(analysis, "post") or not isinstance(analysis.post, ReentrancyDomain):
                    continue

                if analysis.post.variant != DomainVariant.STATE:
                    continue

                state = analysis.post.state

                # Get variables at risk (read before calls and written after)
                vars_at_risk = state.storage_variables_read_before_calls.intersection(
                    state.storage_variables_written.difference(
                        state.storage_variables_written_before_calls
                    )
                )

                # Filter for external calls that DO send ETH
                external_calls_with_eth = set()
                for call in state.external_calls:
                    # Check if the call sends ETH
                    sends_eth = False
                    if call.node in state.send_eth:  # Node marked as sending ETH
                        sends_eth = True
                    else:
                        # Double-check by examining the operations
                        sends_eth = any(self._send_eth(ir) for ir in call.node.irs)

                    if sends_eth:
                        external_calls_with_eth.add(call.node)

                if not (vars_at_risk and external_calls_with_eth):
                    continue

                # Only create findings if we have both vulnerable variables and ETH-sending calls
                variables_written = {var: set() for var in vars_at_risk}
                internal_calls = defaultdict(set)
                internal_variables_written = defaultdict(lambda: defaultdict(set))

                # Track internal calls that lead to ETH-sending external calls
                for ext_call in external_calls_with_eth:
                    if ext_call in state.internal_calls:
                        internal_calls[ext_call] = state.internal_calls[ext_call]

                for node in function.nodes:
                    if node in external_calls_with_eth:
                        continue

                    for var in vars_at_risk:
                        if var in node.state_variables_written:
                            variables_written[var].add(
                                node
                            )  # checks if node writes to vulnerable variable

                # Track variables written in internal calls
                for (
                    internal_call_node,
                    written_vars,
                ) in state.internal_variables_written.items():
                    for var in written_vars:
                        if var not in vars_at_risk:
                            continue

                        internal_function = next(
                            (
                                ir.function
                                for ir in internal_call_node.irs
                                if isinstance(ir, InternalCall)
                            ),
                            None,
                        )

                        if not internal_function:
                            continue

                        # Find nodes that write this variable
                        writing_nodes = {
                            node
                            for node in internal_function.nodes
                            if var in node.state_variables_written
                            or var in node.local_variables_written
                        }

                        internal_variables_written[internal_call_node][var].update(writing_nodes)

                finding = ReentrancyFinding(
                    function=function,
                    external_calls=external_calls_with_eth,
                    variables_written=variables_written,
                    internal_calls=dict(internal_calls),
                    internal_variables_written=dict(
                        {k: dict(v) for k, v in internal_variables_written.items()}
                    ),
                )
                findings.append(finding)

        return findings

    def _detect(self) -> List[Output]:
        super()._detect()

        findings = self.find_reentrancies()
        results = []

        for finding in findings:
            info = ["Reentrancy in ", finding.function, ":\n"]
            info += ["\tExternal calls:\n"]

            internal_calls_printed = set()
            for call in finding.external_calls:
                if call in finding.internal_calls:
                    for internal_call in finding.internal_calls[call]:
                        if internal_call not in internal_calls_printed:
                            info += ["\t- ", internal_call, "\n"]
                            internal_calls_printed.add(internal_call)
                            info += ["\t\t- ", call, "\n"]
                            for nested_call in finding.internal_calls.get(internal_call, []):
                                info += ["\t\t\t- ", nested_call, "\n"]
                else:
                    info += ["\t- ", call, "\n"]

            info += ["\tState variables written after the call(s):\n"]

            # Display variables written in function
            for var, write_nodes in finding.variables_written.items():
                for node in write_nodes:
                    info += ["\t- ", node, "\n"]

            # Display variables written in internal calls
            for internal_call_node, var_writes in finding.internal_variables_written.items():
                if not var_writes:
                    continue
                info += ["\t- ", internal_call_node, "\n"]
                for var, write_nodes in var_writes.items():
                    for node in write_nodes:
                        info += ["\t\t- ", node, "\n"]

            # Cross-function reentrancy information
            all_written_vars = set(finding.variables_written.keys())
            for internal_var_writes in finding.internal_variables_written.values():
                all_written_vars.update(internal_var_writes.keys())

            for var in all_written_vars:
                if isinstance(var, StateVariable):
                    functions_reading = []
                    for contract in self.contracts:
                        for function in contract.functions:
                            if function.is_implemented and var in function.state_variables_read:
                                functions_reading.append(function)

                    if functions_reading:
                        info += [
                            f"\t{var.canonical_name} ({var.source_mapping}) can be used in cross function reentrancies:\n"
                        ]
                        for function in functions_reading:
                            info += [f"\t- {function.canonical_name} ({function.source_mapping})\n"]

            # Create JSON result
            res = self.generate_result(info)
            res.add(finding.function)

            for call in finding.external_calls:
                res.add(call, {"underlying_type": "external_calls_eth", "sends_eth": True})
                # Add internal calls that lead to this external call
                if call in finding.internal_calls:
                    for internal_call in finding.internal_calls[call]:
                        res.add(internal_call, {"underlying_type": "internal_calls"})
                        # Add nested internal calls
                        if internal_call in finding.internal_calls:
                            for nested_call in finding.internal_calls[internal_call]:
                                res.add(nested_call, {"underlying_type": "internal_calls"})

            # Add all variables written in function
            for var, write_nodes in finding.variables_written.items():
                for node in write_nodes:
                    res.add(
                        node,
                        {
                            "underlying_type": "variables_written",
                            "variable_name": var.name,
                            "expression": str(node.expression),
                        },
                    )

            # Add all variables written in internal calls
            for internal_call_node, var_writes in finding.internal_variables_written.items():
                for var, write_nodes in var_writes.items():
                    for node in write_nodes:
                        res.add(
                            node,
                            {
                                "underlying_type": "variables_written_internal",
                                "variable_name": var.name,
                                "expression": str(node.expression),
                                "internal_call": str(internal_call_node),
                            },
                        )

            results.append(res)

        return results
