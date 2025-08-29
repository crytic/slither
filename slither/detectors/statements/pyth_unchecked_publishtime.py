from slither.detectors.abstract_detector import DetectorClassification
from slither.detectors.statements.pyth_unchecked import PythUnchecked


class PythUncheckedPublishTime(PythUnchecked):
    """
    Documentation: This detector finds when the publishTime of a Pyth price is not checked
    """

    ARGUMENT = "pyth-unchecked-publishtime"
    HELP = "Detect when the publishTime of a Pyth price is not checked"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#pyth-unchecked-publishtime"
    )
    WIKI_TITLE = "Pyth unchecked publishTime"
    WIKI_DESCRIPTION = "Detect when the publishTime of a Pyth price is not checked"
    WIKI_RECOMMENDATION = "Check the publishTime of a Pyth price."

    WIKI_EXPLOIT_SCENARIO = """
```solidity
import "@pythnetwork/pyth-sdk-solidity/IPyth.sol";
import "@pythnetwork/pyth-sdk-solidity/PythStructs.sol";

contract C {
    IPyth pyth;

    constructor(IPyth _pyth) {
        pyth = _pyth;
    }

    function bad(bytes32 id) public {
        PythStructs.Price memory price = pyth.getEmaPriceUnsafe(id);
        // Use price
    }
}
```
The function `A` uses the price without checking its `publishTime` coming from the `getEmaPriceUnsafe` function.
"""

    PYTH_FUNCTIONS = [
        "getEmaPrice",
        # "getEmaPriceNoOlderThan",
        "getEmaPriceUnsafe",
        "getPrice",
        # "getPriceNoOlderThan",
        "getPriceUnsafe",
    ]

    PYTH_FIELD = "publishTime"
