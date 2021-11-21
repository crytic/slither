from slither.core.cfg.node import Node, NodeType
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations import Assignment
from slither.slithir.variables import Constant
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification


class ImplicitVisibility(AbstractDetector):

    ARGUMENT = "implicit-visibility"
    HELP = "Null"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#implicit-visibility"

    WIKI_TITLE = "Implicit Visibility"
    WIKI_DESCRIPTION = "Null"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

uint storeduint1 = 15;
uint constant constuint = 16;
uint32 investmentsDeadlineTimeStamp = uint32(now); 

function getConstuint() pure returns(uint256){
    return constuint;
}
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "None"

    def _detect(self):
        """"""
        res = []
        results = []

        for c in self.contracts:
            function = [f for f in c.functions_declared
                        if f.name not in ["slitherConstructorVariables", "slitherConstructorConstantVariables"] 
                    ]
            test = c.variables + function

            for t in test:
                source_map = t.source_mapping
                path = source_map['filename_absolute']
                line = source_map['lines'][0]
                with open(path, 'r') as file:
                    code = file.readlines()[line-1].rstrip()
                if all(vis not in code for vis in ["public", "external", "private", "internal"]):
                    res.append(t)

        if res:
            for r in res:
                info = [r, " does not specify the visibility.\n",]
                res = self.generate_result(info)
                results.append(res)

        return results
