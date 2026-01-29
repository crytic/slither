from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class PythDeprecatedFunctions(AbstractDetector):
    """
    Documentation: This detector finds deprecated Pyth function calls
    """

    ARGUMENT = "pyth-deprecated-functions"
    HELP = "Detect Pyth deprecated functions"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#pyth-deprecated-functions"
    WIKI_TITLE = "Pyth deprecated functions"
    WIKI_DESCRIPTION = "Detect when a Pyth deprecated function is used"
    WIKI_RECOMMENDATION = (
        "Do not use deprecated Pyth functions. Visit https://api-reference.pyth.network/."
    )

    WIKI_EXPLOIT_SCENARIO = """
```solidity
import "@pythnetwork/pyth-sdk-solidity/IPyth.sol";
import "@pythnetwork/pyth-sdk-solidity/PythStructs.sol";

contract C {

    IPyth pyth;

    constructor(IPyth _pyth) {
        pyth = _pyth;
    }

    function A(bytes32 priceId) public {
        PythStructs.Price memory price = pyth.getPrice(priceId);
        ...
    }
}
```
The function `A` uses the deprecated `getPrice` Pyth function.
"""

    def _detect(self):
        DEPRECATED_PYTH_FUNCTIONS = [
            "getValidTimePeriod",
            "getEmaPrice",
            "getPrice",
        ]
        results: list[Output] = []

        for contract in self.compilation_unit.contracts_derived:
            for target_contract, ir in contract.all_high_level_calls:
                if (
                    target_contract.name == "IPyth"
                    and ir.function_name in DEPRECATED_PYTH_FUNCTIONS
                ):
                    info: DETECTOR_INFO = [
                        "The following Pyth deprecated function is used\n\t- ",
                        ir.node,
                        "\n",
                    ]

                    res = self.generate_result(info)
                    results.append(res)

        return results
