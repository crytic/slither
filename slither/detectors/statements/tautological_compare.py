from typing import List
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.slithir.operations import (
    Binary,
    BinaryType,
)

from slither.core.declarations import Function
from slither.utils.output import Output


class TautologicalCompare(AbstractDetector):
    """
    Same variable comparison detector
    """

    ARGUMENT = "tautological-compare"
    HELP = "Comparing a variable to itself always returns true or false, depending on comparison"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#tautological-compare"

    WIKI_TITLE = "Tautological compare"
    WIKI_DESCRIPTION = "A variable compared to itself is probably an error as it will always return `true` for `==`, `>=`, `<=` and always `false` for `<`, `>` and `!=`."
    WIKI_EXPLOIT_SCENARIO = """
```solidity
    function check(uint a) external returns(bool){
        return (a >= a);
    }
```
`check` always return true."""

    WIKI_RECOMMENDATION = "Remove comparison or compare to different value."

    def _check_function(self, f: Function) -> List[Output]:
        affected_nodes = set()
        for node in f.nodes:
            for ir in node.irs:
                if isinstance(ir, Binary):
                    if ir.type in [
                        BinaryType.GREATER,
                        BinaryType.GREATER_EQUAL,
                        BinaryType.LESS,
                        BinaryType.LESS_EQUAL,
                        BinaryType.EQUAL,
                        BinaryType.NOT_EQUAL,
                    ]:
                        if ir.variable_left == ir.variable_right:
                            affected_nodes.add(node)

        results = []
        for n in affected_nodes:
            info: DETECTOR_INFO = [f, " compares a variable to itself:\n\t", n, "\n"]
            res = self.generate_result(info)
            results.append(res)
        return results

    def _detect(self):
        results = []

        for f in self.compilation_unit.functions_and_modifiers:
            results.extend(self._check_function(f))

        return results
