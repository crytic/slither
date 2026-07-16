from slither.slithir.operations.internal_call import InternalCall
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.utils.output import Output


class GelatoUnprotectedRandomness(AbstractDetector):
    """
    Unprotected Gelato VRF requests
    """

    ARGUMENT = "gelato-unprotected-randomness"
    HELP = "Call to _requestRandomness within an unprotected function"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#gelato-unprotected-randomness"

    WIKI_TITLE = "Gelato unprotected randomness"
    WIKI_DESCRIPTION = "Detect calls to `_requestRandomness` within an unprotected function."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C is GelatoVRFConsumerBase {
    function _fulfillRandomness(
        uint256 randomness,
        uint256,
        bytes memory extraData
    ) internal override {
        // Do something with the random number
    }

    function bad() public {
        _requestRandomness(abi.encode(msg.sender));
    }
}
```
The function `bad` is uprotected and requests randomness."""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = (
        "Function that request randomness should be allowed only to authorized users."
    )

    def _detect(self) -> list[Output]:
        results = []

        for contract in self.compilation_unit.contracts_derived:
            if "GelatoVRFConsumerBase" in [c.name for c in contract.inheritance]:
                for function in contract.functions_entry_points:
                    if not function.is_protected() and (
                        nodes_request := [
                            ir.node
                            for ir in function.all_internal_calls()
                            if isinstance(ir, InternalCall)
                            and ir.function_name == "_requestRandomness"
                        ]
                    ):
                        # Sort so output is deterministic
                        nodes_request.sort(key=lambda x: (x.node_id, x.function.full_name))

                        for node in nodes_request:
                            info: DETECTOR_INFO = [
                                function,
                                " is unprotected and request randomness from Gelato VRF\n\t- ",
                                node,
                                "\n",
                            ]
                            res = self.generate_result(info)
                            results.append(res)

        return results
