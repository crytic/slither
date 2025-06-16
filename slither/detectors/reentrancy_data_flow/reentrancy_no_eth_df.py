"""
Re-entrancy detection using data flow analysis

Based on data flow analysis to detect reentrancy vulnerabilities
that affect event ordering and emission
"""

from collections import namedtuple, defaultdict
from typing import DefaultDict, List, Set, Dict, NamedTuple, Any, Tuple

from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.reentrancy import (
    ReentrancyAnalysis,
    ReentrancyDomain,
    DomainVariant,
)
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import Node
from slither.utils.output import Output
from slither.slithir.operations import Send, Transfer, HighLevelCall, LowLevelCall
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable

from loguru import logger


class ReentrancyFinding(NamedTuple):
    """Represents a reentrancy vulnerability finding"""

    function: Function  # Function with reentrancy
    external_calls: Set[Node]  # External calls that can reenter
    variables_written: Dict[
        Variable, Set[Node]
    ]  # Variables written after external calls and their write locations


def to_hashable(data):
    """Convert data to hashable format for use in sets/dicts"""
    if isinstance(data, list):
        return tuple(to_hashable(item) for item in data)
    elif isinstance(data, set):
        return frozenset(to_hashable(item) for item in data)
    elif isinstance(data, dict):
        return tuple(sorted((k, to_hashable(v)) for k, v in data.items()))
    else:
        return data


class ReentrancyNoEthDF(AbstractDetector):
    """
    Reentrancy detector using data flow analysis
    """

    ARGUMENT = "reentrancy-no-eth-df"
    HELP = "Reentrancy vulnerabilities leading to out-of-order Events (data flow analysis)"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-1"
    )

    WIKI_TITLE = "Reentrancy vulnerabilities (data flow)"

    WIKI_DESCRIPTION = """
Detects [reentrancies](https://github.com/trailofbits/not-so-smart-contracts/tree/master/reentrancy) that allow manipulation of the order or value of events using data flow analysis."""

    WIKI_EXPLOIT_SCENARIO = "insert here"
    WIKI_RECOMMENDATION = "Apply the [`check-effects-interactions` pattern](https://docs.soliditylang.org/en/latest/security-considerations.html#re-entrancy)."

    STANDARD_JSON = False

    def __init__(self, compilation_unit, slither_instance, logger_obj):
        super().__init__(compilation_unit, slither_instance, logger_obj)
        self.analysis = ReentrancyAnalysis()

    def find_reentrancies(self) -> List[ReentrancyFinding]:
        """Find all reentrancy vulnerabilities in the contract"""
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

                # Get external calls that do not send ETH
                external_calls_no_eth = set()
                for call in state.external_calls:
                    # Skip if the call is in send_eth
                    if call.node in state.send_eth:
                        # Check if the call actually sends ETH
                        sends_eth = False
                        for ir in call.node.irs:
                            if isinstance(ir, (Send, Transfer, HighLevelCall, LowLevelCall)):
                                if ir.call_value is not None and ir.call_value != 0:
                                    sends_eth = True
                                    break
                        if not sends_eth:
                            external_calls_no_eth.add(call.node)
                    else:
                        external_calls_no_eth.add(call.node)

                if vars_at_risk and external_calls_no_eth:

                    # Initialize variables_written with empty sets
                    variables_written = {var: set() for var in vars_at_risk}

                    # Find nodes where variables are written after external calls
                    for node in function.nodes:
                        # Skip nodes before or at external calls
                        if node in external_calls_no_eth:
                            continue

                        # Add nodes that write to variables at risk
                        for var in vars_at_risk:
                            if var in node.state_variables_written:

                                variables_written[var].add(node)

                    finding = ReentrancyFinding(
                        function=function,
                        external_calls=external_calls_no_eth,
                        variables_written=variables_written,
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
            for call in finding.external_calls:
                info += ["\t- ", call, "\n"]

            info += ["\tState variables written after the call(s):\n"]
            for var, write_nodes in finding.variables_written.items():
                for node in write_nodes:
                    info += ["\t- ", node, "\n"]

            for var in finding.variables_written.keys():
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

            # Create our JSON result
            res = self.generate_result(info)

            res.add(finding.function)

            for call in finding.external_calls:
                res.add(call, {"underlying_type": "external_calls"})

            # Add all variables written
            for var, write_nodes in finding.variables_written.items():
                for node in write_nodes:
                    res.add(
                        node,
                        {
                            "underlying_type": "variables_written",
                            "variable_name": var,
                            "expression": str(node.expression),
                        },
                    )

            results.append(res)

        return results
