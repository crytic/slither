from typing import List

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class ChainlinkFeedRegistry(AbstractDetector):

    ARGUMENT = "chainlink-feed-registry"
    HELP = "Detect when chainlink feed registry is used"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#chainlink-feed-registry-usage"

    WIKI_TITLE = "Chainlink Feed Registry usage"
    WIKI_DESCRIPTION = "Detect when Chainlink Feed Registry is used. At the moment is only available on Ethereum Mainnet."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
import "chainlink/contracts/src/v0.8/interfaces/FeedRegistryInteface.sol"

contract A {
    FeedRegistryInterface public immutable registry;

    constructor(address _registry) {
        registry = _registry;
    }

    function getPrice(address base, address quote) public return(uint256) {
        (, int256 price,,,) = registry.latestRoundData(base, quote);
        // Do price validation
        return uint256(price);
    }
}    
```
If the contract is deployed on a different chain than Ethereum Mainnet the `getPrice` function will revert.
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Do not use Chainlink Feed Registry outside of Ethereum Mainnet."

    def _detect(self) -> List[Output]:
        # https://github.com/smartcontractkit/chainlink/blob/8ca41fc8f722accfccccb4b1778db2df8fef5437/contracts/src/v0.8/interfaces/FeedRegistryInterface.sol
        registry_functions = [
            "decimals",
            "description",
            "versiom",
            "latestRoundData",
            "getRoundData",
            "latestAnswer",
            "latestTimestamp",
            "latestRound",
            "getAnswer",
            "getTimestamp",
            "getFeed",
            "getPhaseFeed",
            "isFeedEnabled",
            "getPhase",
            "getRoundFeed",
            "getPhaseRange",
            "getPreviousRoundId",
            "getNextRoundId",
            "proposeFeed",
            "confirmFeed",
            "getProposedFeed",
            "proposedGetRoundData",
            "proposedLatestRoundData",
            "getCurrentPhaseId",
        ]
        results = []

        for contract in self.compilation_unit.contracts_derived:
            nodes = []
            for target, ir in contract.all_high_level_calls:
                if (
                    target.name == "FeedRegistryInterface"
                    and ir.function_name in registry_functions
                ):
                    nodes.append(ir.node)
            # Sort so output is deterministic
            nodes.sort(key=lambda x: (x.node_id, x.function.full_name))

            if len(nodes) > 0:
                info: DETECTOR_INFO = [
                    "The Chainlink Feed Registry is used in the ",
                    contract.name,
                    " contract. It's only available on Ethereum Mainnet, consider to not use it if the contract needs to be deployed on other chains.\n",
                ]

                for node in nodes:
                    info.extend(["\t - ", node, "\n"])

                res = self.generate_result(info)
                results.append(res)

        return results
