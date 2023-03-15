"""
Module detecting unused return values from send
"""

from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.operations.unused_return_values import UnusedReturnValues
from slither.slithir.operations import Send
from slither.slithir.operations.operation import Operation


class UncheckedSend(UnusedReturnValues):
    """
    If the return value of a send is not checked, it might lead to losing ether
    """

    ARGUMENT = "unchecked-send"
    HELP = "Unchecked send"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-send"

    WIKI_TITLE = "Unchecked Send"
    WIKI_DESCRIPTION = "The return value of a `send` is not checked."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MyConc{
    function my_func(address payable dst) public payable{
        dst.send(msg.value);
    }
}
```
The return value of `send` is not checked, so if the send fails, the Ether will be locked in the contract.
If `send` is used to prevent blocking operations, consider logging the failed `send`.
    """
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Ensure that the return value of `send` is checked or logged."

    def _is_instance(self, ir: Operation) -> bool:  # pylint: disable=no-self-use
        return isinstance(ir, Send)
