from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import Return
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations.assignment import Assignment
from slither.slithir.variables.reference import ReferenceVariable


class PriVarBeAccessed(AbstractDetector):
    ARGUMENT = "pri-var-be-accessed"
    HELP = "Null"
    IMPACT = DetectorClassification.LOW
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#pri-var-be-access"
    WIKI_TITLE = "privary variables be accessed by public function"
    WIKI_DESCRIPTION = "Null"

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

uint private owner;
function resetOwner() external {
    owner = 0;
}
```
 external function accesses private variable, which may lead to accidental exposure of privacy"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "dont access by public function."

    def _detect(self):
        """"""
        node = []
        res = []
        results = []

        for c in self.contracts:
            state_var = [v for v in c.variables if v.visibility in ["private", "internal"]]
            for f in c.functions_declared:
                if f.is_constructor:
                    continue
                if f.name in ["slitherConstructorVariables", "slitherConstructorConstantVariables"]:
                    continue
                
                if f.visibility not in ["public", "external"]:
                    continue

                for n in f.nodes:
                    for ir in n.irs:
                        if isinstance(ir, Return):
                            for ret in ir.values:
                                if isinstance(ret, ReferenceVariable):
                                    ret = ret.type

                                if not isinstance(ret, StateVariable):
                                    continue

                                if ret in state_var:
                                    node.append(n)
                                    break

                        elif isinstance(ir, Assignment):
                            left = ir.lvalue
                            if isinstance(left, ReferenceVariable):
                                left = left.type
                            
                            if not isinstance(left, StateVariable):
                                continue

                            if left in state_var:
                                node.append(n)
                                break

        if node:
            for r in node:
                info = [r, " hav private variable been accessed or modified.\n",]
                res = self.generate_result(info)
                results.append(res)

        return results
