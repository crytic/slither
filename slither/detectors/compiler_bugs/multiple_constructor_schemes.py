from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class MultipleConstructorSchemes(AbstractDetector):
    """
    Module detecting multiple constructors in the same contract.
    (This was possible prior to Solidity 0.4.23, using old and new constructor schemes).
    """

    ARGUMENT = "multiple-constructors"
    HELP = "Multiple constructor schemes"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#multiple-constructor-schemes"
    )

    WIKI_TITLE = "Multiple constructor schemes"
    WIKI_DESCRIPTION = (
        "Detect multiple constructor definitions in the same contract (using new and old schemes)."
    )
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract A {
    uint x;
    constructor() public {
        x = 0;
    }
    function A() public {
        x = 1;
    }
    
    function test() public returns(uint) {
        return x;
    }
}
```
In Solidity [0.4.22](https://github.com/ethereum/solidity/releases/tag/v0.4.23), a contract with both constructor schemes will compile. The first constructor will take precedence over the second, which may be unintended."""

    WIKI_RECOMMENDATION = "Only declare one constructor, preferably using the new scheme `constructor(...)` instead of `function <contractName>(...)`."

    def _detect(self):
        """
        Detect multiple constructor schemes in the same contract
        :return: Returns a list of contract JSON result, where each result contains all constructor definitions.
        """
        results = []
        for contract in self.contracts:
            # Obtain any constructors defined in this contract
            constructors = [f for f in contract.constructors if f.contract_declarer == contract]

            # If there is more than one, we encountered the described issue occurring.
            if constructors and len(constructors) > 1:
                info = [contract, " contains multiple constructors in the same contract:\n"]
                for constructor in constructors:
                    info += ["\t- ", constructor, "\n"]

                res = self.generate_result(info)
                results.append(res)

        return results
