"""
Module detecting unused return values from low level
"""
from slither.detectors.abstract_detector import DetectorClassification
from .unused_return_values import UnusedReturnValues
from slither.slithir.operations import LowLevelCall

class UncheckedLowLevel(UnusedReturnValues):
    """
    If the return value of a send is not checked, it might lead to losing ether
    """

    ARGUMENT = 'unchecked-lowlevel'
    HELP = 'Unchecked low-level calls'
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = 'https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-low-level-calls'

    WIKI_TITLE = 'Unchecked low-level calls'
    WIKI_DESCRIPTION = 'The return value of a low-level call is not checked.'
    WIKI_EXPLOIT_SCENARIO = '''
```solidity
contract MyConc{
    function my_func(address payable dst) public payable{
        dst.call.value(msg.value)("");
    }
}
```
The return value of the low-level call is not checked, so if the call fails, the Ether will be locked in the contract.
If the low level is used to prevent blocking operations, consider logging failed calls.
    '''

    WIKI_RECOMMENDATION = 'Ensure that the return value of a low-level call is checked or logged.'

    _txt_description = "low-level calls"

    def _is_instance(self, ir):
        return isinstance(ir, LowLevelCall)




