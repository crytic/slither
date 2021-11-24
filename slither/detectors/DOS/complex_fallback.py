from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ComplexFallbackFunction(AbstractDetector):

    ARGUMENT = "complex-fallback"
    HELP = "complex fallcak function does not set up a separate function"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#complex-fallback"

    WIKI_TITLE = "Complex Fallback Function"
    WIKI_DESCRIPTION = "Complex fallcak function does not set up a separate function."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

fallback() external payable{
    require(msg.value > 0);
    for(uint256 i = 0; i < payer.length; i++){
        if(msg.sender == payer[i])
            money[i] += msg.value;
    }
}
the contract always uses the fallback function by default to respond to transfers. In general, most contracts use send-statements or transfer-statements to send ethers, both of which carry only 2300 gas. When the fallback function of the contract consumes more than 2300 gas, the transfer will fail.
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Set up a separate function, and call the function through a call-statement."

    def _detect(self):
        """"""
        results = []

        for c in self.contracts:
            fallback = [f for f in c.functions_declared if f.is_fallback]

            if not fallback:
                continue
            if len(fallback[0].nodes) <= 1:
                continue

            info = [fallback[0], " is a complex fallbeck function, but not a separate name.\n",]
            res = self.generate_result(info)
            results.append(res)

        return results
