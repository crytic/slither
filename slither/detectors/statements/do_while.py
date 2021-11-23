from slither.core.cfg.node import NodeType
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ContinueInDoWhile(AbstractDetector):

    ARGUMENT = "do-continue-while"
    HELP = "use continue in do-while loop"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#do-continue-while"

    WIKI_TITLE = "Continue In do-while Loop"
    WIKI_DESCRIPTION = "Prior to version 0.5.0 of solidity, there was a bug with using the do-while-statement. Using the continue-statement in the do-while-statement causes the bug to skip the conditional judgment and go directly to the loop body for execution again."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

function deleteOwner(address _own) external onlyOwner{
        uint256 i = 0;
        uint256 _length = owners.length;
        do{
            continue;
            i++;
        }while( i < _length);
    }
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Don't use continue"

    @staticmethod
    def detect_continue(f):
        res = []
        for node in f.nodes:
            if node.type == NodeType.CONTINUE:
                if node.sons[0].type == NodeType.STARTLOOP:
                    res.append(node)
        return res


    def _detect(self):
        """"""
        results = []

        for c in self.contracts:
            for f in c.functions_declared:
                values = self.detect_continue(f)
            
                if not values:
                    continue
                
                for var in values:
                    info = [var, " use continue in do-while loop\n",]

                    res = self.generate_result(info)
                    results.append(res)

        return results
