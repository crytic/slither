from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, BinaryType, Assignment, Length
from slither.slithir.operations.index import Index
from slither.slithir.variables import Constant,  ReferenceVariable, TemporaryVariable

class StorageOverleap(AbstractDetector):

    ARGUMENT = "storage-overleap"
    HELP = "writing to arbitrary storage location"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#storage-overleap"

    WIKI_TITLE = "Signature with Wrong Parameters"
    WIKI_DESCRIPTION = " "

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou
uint[] private bonusCodes;

//bonusCodes.length can be underflow
function PopBonusCode() external {
    require(0 <= bonusCodes.length);
    bonusCodes.pop();
}
    
function UpdateBonusCodeAt(uint idx, uint c) external {
    require(idx < bonusCodes.length);
    bonusCodes[idx] = c;
}
```
"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "don't let length be underflow"
    @staticmethod
    def detect_continue(f, underflow_rec):
        length = dict()
        index = dict()
        check = []
        check_id = []
        underflow = []
        res = []

        for node in f.nodes:
            for ir in node.irs:
                if isinstance(ir, Length):
                    length[ir.lvalue] = [ir.value]

                elif isinstance(ir, Assignment):
                    (L, R) = ir.variables
                    if isinstance(L, Constant) or isinstance(R, Constant):
                        continue

                    if R in length:
                        length[L] = length[R]
                    
                    elif R in index:
                        index[L] = index[R]

                    #step4 : may be cause storage overleap, store node
                    elif L in index and index[L] in check_id:
                        res.append(node)

                elif isinstance(ir, Index):
                    (v, i) = ir.read

                    if isinstance(v, (ReferenceVariable, TemporaryVariable)) and (v in index):
                        v = index[v]
                        if len(var) == 1:
                            var = var[0]

                    if (not isinstance(i, Constant) and 
                        isinstance(i, (ReferenceVariable, TemporaryVariable)) and 
                        i in index
                    ):
                        i = index[i]
                        if len(i) == 1:
                            i = i[0]
                    
                    index[ir.lvalue] = (v, i)
                
                elif isinstance(ir, Binary):
                    (L, R) = ir.read

                    #step1 : check length, store safe condition (no underflow's condition)
                    if ir.type in [BinaryType.GREATER_EQUAL, BinaryType.LESS_EQUAL]:
                        if isinstance(L, Constant) and int(L.name) > 0 and R in length:
                            check.append(length[R])

                        elif isinstance(R, Constant) and int(R.name) > 0 and L in length:
                            check.append(length[L])
                    #step1 :
                    if ir.type in [BinaryType.GREATER, BinaryType.LESS, BinaryType.EQUAL, BinaryType.NOT_EQUAL]:
                        if isinstance(L, Constant) and int(L.name) >= 0 and R in length:
                            check.append(length[R])

                        elif isinstance(R, Constant) and int(R.name) >= 0 and L in length:
                            check.append(length[L])
                    
                    #step3 : when length can be underflow, the require-statement is always true, record it.
                    if ir.type in [BinaryType.GREATER, BinaryType.LESS]:
                        if isinstance(L, Constant) or isinstance(R, Constant):
                            continue
                        if L in length and (length[L] in underflow or length[L] in underflow_rec):
                            check_id.append((length[L][0], R))
                        if R in length and (length[R] in underflow or length[R] in underflow_rec):
                            check_id.append((length[R][0], L))

                    #step2 : if length-- and not in check list, store it
                    if ir.type == BinaryType.SUBTRACTION:
                        if L in length and length[L] not in check:
                            underflow.append(length[L])

        return [res, underflow]


    def _detect(self):
        """"""
        results = []
        values_rec = []
        underflow_rec = []
        for c in self.contracts:
            for f in c.functions:
                (values, underflow) = self.detect_continue(f, underflow_rec)
                underflow_rec += underflow
            
                if not values:
                    continue
                
                for var in values:
                    if var in values_rec:
                        values.remove(var)
                        continue

                    info = [var, " cause writing to arbitrary storage location.\n",]
                    res = self.generate_result(info)
                    results.append(res)
                
                values_rec += values

        return results
