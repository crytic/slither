from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.statements.pyth_unchecked import PythUnchecked


class PythUncheckedConfidence(PythUnchecked):
    """
    Documentation: This detector finds when the confidence level of a Pyth price is not checked
    """

    ARGUMENT = "pyth-unchecked-confidence"
    HELP = "Detect when the confidence level of a Pyth price is not checked"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#pyth-unchecked-confidence-level"
    WIKI_TITLE = "Pyth unchecked confidence level"
    WIKI_DESCRIPTION = "Detect when the confidence level of a Pyth price is not checked"
    WIKI_RECOMMENDATION = "Check the confidence level of a Pyth price. Visit https://docs.pyth.network/price-feeds/best-practices#confidence-intervals for more information."

    WIKI_EXPLOIT_SCENARIO = """
```solidity
import "@pythnetwork/pyth-sdk-solidity/IPyth.sol";
import "@pythnetwork/pyth-sdk-solidity/PythStructs.sol";

contract C {
    IPyth pyth;

    constructor(IPyth _pyth) {
        pyth = _pyth;
    }

    function bad(bytes32 id, uint256 age) public {
        PythStructs.Price memory price = pyth.getEmaPriceNoOlderThan(id, age);
        // Use price
    }
}    
```
The function `A` uses the price without checking its confidence level. 
"""

    PYTH_FUNCTIONS = [
        "getEmaPrice",
        "getEmaPriceNoOlderThan",
        "getEmaPriceUnsafe",
        "getPrice",
        "getPriceNoOlderThan",
        "getPriceUnsafe",
    ]

    PYTH_FIELD = "conf"
