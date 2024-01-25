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

    ARGUMENT = "deprecated_chainlink_call" 
    HELP = "Oracle vulnerabilities"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "TODO: Will be added later."
    WIKI_TITLE = "Oracle vulnerabilities"
    WIKI_DESCRIPTION = "Detection of deprecated Chainlink calls."
    WIKI_RECOMMENDATION = "Do not use deprecated Chainlink calls. Visit https://docs.chain.link/data-feeds/api-reference/ for more information."
    WIKI_EXPLOIT_SCENARIO = ""

    DEPRECATED_CHAINLINK_CALLS = ["getAnswer", "getTimestamp", "latestAnswer", "latestRound", "latestTimestamp"]

    def find_usage_of_deprecated_chainlink_calls(self, contracts : Contract):
        """
        Find usage of deprecated Chainlink calls in the contracts.
        """
        results = []
        for contract in contracts:
            for function in contract.functions:
                for node in function.nodes:
                    for ir in node.irs:
                        if isinstance(ir, HighLevelCall):
                            if ir.function.name in self.DEPRECATED_CHAINLINK_CALLS and str(ir.destination.type) == "AggregatorV3Interface":
                                results.append(f"Deprecated Chainlink call {ir.destination}.{ir.function.name} used ({node.source_mapping}).\n")
        return results

    def _detect(self):
        results = self.find_usage_of_deprecated_chainlink_calls(self.contracts)
        if len(results) > 0:
            res = self.generate_result(results)
            return [res]
        return []