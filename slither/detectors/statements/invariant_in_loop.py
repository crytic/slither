from collections import defaultdict
from slither.core.cfg.node import NodeType
from slither.slithir.variables import Constant
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Length, Binary, Assignment
from slither.slithir.operations.binary import BinaryType


class InvariantInLoop(AbstractDetector):

    ARGUMENT = "invariant-in-loop"
    HELP = "Invariant is calculated for each loop"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation/#invariant-in-loop"

    WIKI_TITLE = "Invariant In Loop"
    WIKI_DESCRIPTION = "Extracting invariants from loops is a widely used method to optimize performance. In Ethereum, this action can also reduce the loss of gas."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
//from JiuZhou

function addOne() public{
	for(uint256 i = 0; i < grades.length; i++){
		grades[i] += 1;
	}
}
```
The array length is calculated for each loop, but the array length remains the same"""
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Extracting invariants from loops"

    @staticmethod
    def detect_array_of_byte(f):
        flag = None
        invariant = []
        var = defaultdict(list)
        var_rev = defaultdict(list)
        used_node = []
        tmp_n=[]
        tmp_id=[]
        
        nodes = f.nodes
        id = 0
        while True:
            if id == len(nodes):
                break

            if nodes[id] in used_node:
                if flag == True:
                    invariant += [var[k] for k in var]
                    id = tmp_id.pop()
                    nodes = tmp_n.pop()
                    flag = False
                id = id+1

            if nodes[id].type == NodeType.IFLOOP:
                var.clear()
                var_rev.clear()
                
                tmp_n.append(nodes)
                tmp_id.append(id)
                
                nodes = [nodes[id],nodes[id].son_true]
                id = 0
                flag = True

            elif flag == True and len(tmp_n) > 0:
                nodes += [son for son in nodes[id].sons]
                    
            
            if flag == True:
                for ir in nodes[id].irs:
                    if isinstance(ir, Length):
                        var[ir.lvalue] = ir.value
                        var_rev[ir.value].append(ir.lvalue)

                    elif (isinstance(ir, Assignment)):
                        if not isinstance(ir.lvalue, Constant) and ir.lvalue in var:
                            pop_value = var.pop(ir.lvalue)
                            var_rev[pop_value].remove(ir.lvalue)

                            for v in var_rev[pop_value]:
                                var.pop(v)

                            var_rev.pop(pop_value)

                    elif (isinstance(ir, Binary) and
                         (ir.type == BinaryType.ADDITION or ir.type == BinaryType.SUBTRACTION)
                    ):
                        for read in ir.read:
                            if not isinstance(read, Constant) and read in var:
                                pop_value = var.pop(read)
                                var_rev[pop_value].remove(read)
                            
                                for v in var_rev[pop_value]:
                                    var.pop(v)

                                var_rev.pop(pop_value)
                    
            used_node.append(nodes[id])
            id = id +1
            if id  == len(nodes):
                break
        
        return invariant

    def _detect(self):
        """"""
        results = []

        for c in self.contracts:
            for f in c.functions_declared:
                values = self.detect_array_of_byte(f)
            
                if not values:
                    continue
                
                for var in values:
                    info = [var, " be calculated for each loop, but the array length remains the same.\n",]

                    res = self.generate_result(info)
                    results.append(res)

        return results
