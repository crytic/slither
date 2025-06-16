"""
Re-entrancy detection using data flow analysis

Based on data flow analysis to detect reentrancy vulnerabilities
that affect event ordering and emission
"""

from collections import namedtuple, defaultdict
from typing import DefaultDict, List, Set, Dict

from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.reentrancy import (
    ReentrancyAnalysis,
    ReentrancyDomain,
    DomainVariant,
)
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.core.cfg.node import Node
from slither.utils.output import Output

FindingKey = namedtuple("FindingKey", ["function", "calls", "send_eth"])
FindingValue = namedtuple("FindingValue", ["variable", "node", "nodes"])


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


class ReentrancyEventsDF(AbstractDetector):
    """
    Reentrancy detector using data flow analysis
    """

    ARGUMENT = "reentrancy-eth-df"
    HELP = "Reentrancy vulnerabilities leading to out-of-order Events (data flow analysis)"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#reentrancy-vulnerabilities-3"
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

    def find_reentrancies(self) -> DefaultDict[FindingKey, Set[FindingValue]]:
        result = defaultdict(set)

        functions = [f for c in self.contracts for f in c.functions if f.is_implemented]
        vulnerable_functions = []

        for function in functions:
            func_name = str(function.name)

            # Run reentrancy analysis
            engine = Engine.new(analysis=ReentrancyAnalysis(), functions=[function])
            engine.run_analysis()
            results = engine.result()

            # Check for vulnerability
            is_vulnerable = False
            vulnerable_events = []

            for node, analysis in results.items():
                if not hasattr(analysis, "post") or not isinstance(analysis.post, ReentrancyDomain):
                    continue

                if analysis.post.variant != DomainVariant.STATE:
                    continue

                state = analysis.post.state

                # Check for reentrancy event pattern: call emitted before event
                calls_after_events = state.calls_emitted_after_events.intersection(
                    state.external_calls
                )

                if calls_after_events:
                    is_vulnerable = True
                    finding_key = FindingKey(
                        function=function,
                        calls=to_hashable(calls_after_events),
                        send_eth=to_hashable(set()),
                    )
                    finding_values = {
                        FindingValue(
                            event,
                            event.node,
                            tuple(sorted(calls_after_events, key=lambda x: x.node.node_id)),
                        )
                        for event in state.events
                    }
                    if finding_values:
                        result[finding_key] |= finding_values
                    vulnerable_events.extend(
                        [call.node.function.name for call in calls_after_events]
                    )

            if is_vulnerable:
                vulnerable_functions.append(func_name)

        return result

    def _detect(self) -> List[Output]:
        super()._detect()

        reentrancies = self.find_reentrancies()
        results = []

        result_sorted = sorted(list(reentrancies.items()), key=lambda x: x[0][0].name)
        for (func, calls, send_eth), events in result_sorted:
            info = ["Reentrancy in ", func, ":\n"]
            info += ["\tExternal calls:\n"]
            for call in calls:
                info += ["\t- ", call.node, "\n"]
            if calls != send_eth and send_eth:
                info += ["\tExternal calls sending eth:\n"]
                for call in send_eth:
                    info += ["\t- ", call.node, "\n"]
            info += ["\tEvent emitted after the call(s):\n"]
            for finding_value in events:
                info += ["\t- ", finding_value.node, "\n"]

            res = self.generate_result(info)

            res.add(func)

            for call in calls:
                res.add(call.node, {"underlying_type": "external_calls"})

            if calls != send_eth:
                for call in send_eth:
                    res.add(call.node, {"underlying_type": "external_calls_sending_eth"})

            for finding_value in events:
                res.add(finding_value.node, {"underlying_type": "event"})

            results.append(res)

        return results
