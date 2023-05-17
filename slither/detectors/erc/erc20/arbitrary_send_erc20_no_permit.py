from typing import List
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output
from .arbitrary_send_erc20 import ArbitrarySendErc20


class ArbitrarySendErc20NoPermit(AbstractDetector):
    """
    Detect when `msg.sender` is not used as `from` in transferFrom
    """

    ARGUMENT = "arbitrary-send-erc20"
    HELP = "transferFrom uses arbitrary `from`"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#arbitrary-from-in-transferfrom"

    WIKI_TITLE = "Arbitrary `from` in transferFrom"
    WIKI_DESCRIPTION = "Detect when `msg.sender` is not used as `from` in transferFrom."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    function a(address from, address to, uint256 amount) public {
        erc20.transferFrom(from, to, am);
    }
```
Alice approves this contract to spend her ERC20 tokens. Bob can call `a` and specify Alice's address as the `from` parameter in `transferFrom`, allowing him to transfer Alice's tokens to himself."""

    WIKI_RECOMMENDATION = """
Use `msg.sender` as `from` in transferFrom.
"""

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []

        arbitrary_sends = ArbitrarySendErc20(self.compilation_unit)
        arbitrary_sends.detect()
        for node in arbitrary_sends.no_permit_results:
            func = node.function
            info: DETECTOR_INFO = [func, " uses arbitrary from in transferFrom: ", node, "\n"]
            res = self.generate_result(info)
            results.append(res)

        return results
