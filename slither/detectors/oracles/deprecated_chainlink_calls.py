from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.declarations.contract import Contract
from slither.slithir.operations import HighLevelCall

class DeprecatedChainlinkCalls(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = "deprecated_chainlink_call"  # slither will launch the detector with slither.py --detect mydetector
    HELP = "Help printed by slither"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "RUN"

    WIKI_TITLE = "asda"
    WIKI_DESCRIPTION = "Slot0 is vulnerable to price manipulation as it gets price at the current moment. TWAP should be used instead."
    WIKI_EXPLOIT_SCENARIO = "asdsad"
    WIKI_RECOMMENDATION = "asdsad"

    DEPRECATED_CHAINLINK_CALLS = ["getAnswer", "getTimestamp", "latestAnswer", "latestRound", "latestTimestamp"]

    def find_usage_of_deprecated_chainlink_calls(self, contracts : Contract):
        results = []
        for contract in contracts:
            for function in contract.functions:
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, HighLevelCall): # TODO ADd interface check
                            if ir.function.name in self.DEPRECATED_CHAINLINK_CALLS and str(ir.destination.type) == "AggregatorV3Interface":
                                results.append(f"Deprecated Chainlink call {ir.function.name} found in {node.source_mapping}")
        return results

    def _detect(self):
        results = self.find_usage_of_deprecated_chainlink_calls(self.contracts)
        if len(results) > 0:
            res = self.generate_result(results)
            return [res]
        return []