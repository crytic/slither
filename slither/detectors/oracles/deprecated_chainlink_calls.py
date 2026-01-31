from slither.core.declarations.contract import Contract
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import HighLevelCall


class DeprecatedChainlinkCall(AbstractDetector):
    """
    Documentation: This detector scans for deprecated Chainlink API calls in Solidity contracts. For example, it flags the use of `getAnswer` which is no longer recommended.
    """

    ARGUMENT = "deprecated-chainlink-call"
    HELP = "Oracle vulnerabilities"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#deprecated-chainlink-call"
    WIKI_TITLE = "Deprecated Chainlink call"
    WIKI_DESCRIPTION = "Detection of deprecated Chainlink call."
    WIKI_RECOMMENDATION = "Do not use deprecated Chainlink calls. Visit https://docs.chain.link/data-feeds/api-reference/ for active API calls."
    WIKI_EXPLOIT_SCENARIO = "---"

    DEPRECATED_CHAINLINK_CALLS = [
        "getAnswer",
        "getTimestamp",
        "latestAnswer",
        "latestRound",
        "latestTimestamp",
    ]

    def is_old_chainlink_call(self, ir) -> bool:
        """
        Check if the given operation is an old Chainlink call.
        """
        if isinstance(ir, HighLevelCall):
            if (
                ir.function.name in self.DEPRECATED_CHAINLINK_CALLS
                and str(ir.destination.type) == "AggregatorV3Interface"
            ):
                return True
        return False

    def find_usage_of_deprecated_chainlink_calls(self, contracts: Contract):
        """
        Find usage of deprecated Chainlink calls in the contracts.
        """
        results = []
        for contract in contracts:
            for function in contract.functions:
                for node in function.nodes:
                    for ir in node.irs:
                        if self.is_old_chainlink_call(ir):
                            results.append(
                                f"Deprecated Chainlink call {ir.destination}.{ir.function.name} used ({node.source_mapping}).\n"
                            )
        return results

    def _detect(self):
        results = self.find_usage_of_deprecated_chainlink_calls(self.contracts)
        if len(results) > 0:
            res = self.generate_result(results)
            return [res]
        return []
