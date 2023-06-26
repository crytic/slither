from typing import List

from slither.core.cfg.node import Node
from slither.core.declarations import Function, SolidityVariable
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.utils.output import Output


class VarReadUsingThis(AbstractDetector):
    ARGUMENT = "var-read-using-this"
    HELP = "Contract reads its own variable using `this`"
    IMPACT = DetectorClassification.OPTIMIZATION
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#public-variable-read-in-external-context"

    WIKI_TITLE = "Public variable read in external context"
    WIKI_DESCRIPTION = "The contract reads its own variable using `this`, adding overhead of an unnecessary STATICCALL."
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

    def _detect(self) -> List[Output]:
        results = []
        for c in self.contracts:
            for func in c.functions:
                for node in self._detect_var_read_using_this(func):
                    info: DETECTOR_INFO = [
                        "The function ",
                        func,
                        " reads ",
                        node,
                        " with `this` which adds an extra STATICCALL.\n",
                    ]
                    json = self.generate_result(info)
                    results.append(json)

        return results

    @staticmethod
    def _detect_var_read_using_this(func: Function) -> List[Node]:
        results: List[Node] = []
        for node in func.nodes:
            for ir in node.irs:
                if isinstance(ir, HighLevelCall):
                    if (
                        ir.destination == SolidityVariable("this")
                        and ir.is_static_call()
                        and ir.function.visibility == "public"
                    ):
                        results.append(node)
        return sorted(results, key=lambda x: x.node_id)
