from typing import List
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output
from .arbitrary_send_erc20 import ArbitrarySendErc20


class ArbitrarySendErc20Permit(AbstractDetector):
    """
    Detect when `msg.sender` is not used as `from` in transferFrom along with the use of permit.
    """

    ARGUMENT = "arbitrary-send-erc20-permit"
    HELP = "transferFrom uses arbitrary from with permit"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/trailofbits/slither/wiki/Detector-Documentation#arbitrary-send-erc20-permit"

    WIKI_TITLE = "Arbitrary `from` in transferFrom used with permit"
    WIKI_DESCRIPTION = (
        "Detect when `msg.sender` is not used as `from` in transferFrom and permit is used."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    function bad(address from, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s, address to) public {
        erc20.permit(from, address(this), value, deadline, v, r, s);
        erc20.transferFrom(from, to, value);
    }
```
If an ERC20 token does not implement permit and has a fallback function e.g. WETH, transferFrom allows an attacker to transfer all tokens approved for this contract."""

    WIKI_RECOMMENDATION = """
Ensure that the underlying ERC20 token correctly implements a permit function.
"""

    def _detect(self) -> List[Output]:
        """"""
        results: List[Output] = []

        arbitrary_sends = ArbitrarySendErc20(self.compilation_unit)
        arbitrary_sends.detect()
        for node in arbitrary_sends.permit_results:
            func = node.function
            info = [
                func,
                " uses arbitrary from in transferFrom in combination with permit: ",
                node,
                "\n",
            ]
            res = self.generate_result(info)
            results.append(res)

        return results
