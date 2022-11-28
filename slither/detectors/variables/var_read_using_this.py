from typing import List
from slither.core.declarations import Function, SolidityVariable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations.high_level_call import HighLevelCall


class VarReadUsingThis(AbstractDetector):
    ARGUMENT = "var-read-using-this"
    HELP = "Contract reads its own variable using `this`"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/trailofbits/slither-private/wiki/Vulnerabilities-Description#var-read-using-this"

    WIKI_TITLE = "Variable read using this"
    WIKI_DESCRIPTION = "Contract reads its own variable using `this`, adding overhead of an unnecessary STATICCALL."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract C {
    mapping(uint => address) public myMap;
    function test(uint x) external returns(address) {
        return this.myMap(x);
    }
}
```
"""

    WIKI_RECOMMENDATION = "Read the variable directly from storage instead of calling the contract."

    def _detect(self):
        results = []
        for c in self.contracts:
            for func in c.functions:
                for node in self._detect_var_read_using_this(func):
                    info = [
                        "The function ",
                        func,
                        " reads ",
                        node,
                        " with `this` which adds an extra STATICALL.\n",
                    ]
                    json = self.generate_result(info)
                    results.append(json)

        return results

    def _detect_var_read_using_this(self, func: Function) -> List:
        results = []
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, HighLevelCall):
                    if ir.destination == SolidityVariable("this") and ir.is_static_call():
                        results.append(node)
        return results
