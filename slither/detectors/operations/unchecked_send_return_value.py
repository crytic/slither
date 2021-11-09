"""
Module detecting unused return values from send
"""

from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Unpack, BinaryType, Binary, Assignment,Unary, SolidityCall, Condition,  Send
from slither.slithir.variables.constant import Constant
from slither.core.cfg.node import NodeType
from slither.core.variables.state_variable import StateVariable


class UncheckedSend(AbstractDetector):
    """
    If the return value of a send is not checked, it might lead to losing ether
    """

    ARGUMENT = "unchecked-send"
    HELP = "Unchecked send"
    IMPACT = DetectorClassification.MEDIUM
    CONFIDENCE = DetectorClassification.MEDIUM

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unchecked-send"

    WIKI_TITLE = "Unchecked Send"
    WIKI_DESCRIPTION = "The return value of a `send` is not checked."

    # region wiki_exploit_scenario
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract MyConc{
    function my_func(address payable dst) public payable{
        dst.send(msg.value);
    }
}
```
The return value of `send` is not checked, so if the send fails, the Ether will be locked in the contract.
If `send` is used to prevent blocking operations, consider logging the failed `send`.
    """
    # endregion wiki_exploit_scenario

    WIKI_RECOMMENDATION = "Ensure that the return value of `send` is checked or logged."

    def _is_instance(self, ir):  # pylint: disable=no-self-use
        return isinstance(ir, Send)
    def detect_unused_return_values(self, f):  # pylint: disable=no-self-use
        """
            Return the nodes where the return value of a call is unused
        Args:
            f (Function)
        Returns:
            list(Node)
        """

        bugs_f = []
        bugs = {}
        nodes_origin = {}

        cond_bug_node = []
        check_node = []
        check_end = []
        nodeID = []
        if_start_count = []
        if_end_count = []
        id = -1

        for n in f.nodes:
            if (id >= 0) and (check_node[id] <= n.node_id):
                if (check_end[id] == -1) or (check_end[id] > n.node_id):
                    if n.type == NodeType.THROW:
                        check_node[id] = -1

                    elif len(n.irs):
                        ir = n.irs[0]
                        if isinstance(ir, SolidityCall) and ir.function.name in ["revert(string)","revert()"]:
                            check_node[id] = -1

                if check_node[id] == -1:
                    id -= 1
                    cond_bug_node.pop()
                    check_node.pop()
                    check_end.pop()
                    nodeID.pop()
                    if_end_count.pop()
                    if_start_count.pop()
                    continue

                if (n.type == NodeType.IF) or (n.type == NodeType.IFLOOP):
                    if_start_count[id] += 1
                if n.type == NodeType.ENDIF:
                    if_end_count[id] += 1

                if check_node[id] != -1 and if_start_count[id] == if_end_count[id]:
                    if (n.node_id - nodeID[id] > if_start_count[id]
                        and cond_bug_node[id] in nodes_origin
                    ):
                        nodes_origin.pop(cond_bug_node[id])
                        id -= 1
                        cond_bug_node.pop()
                        check_node.pop()
                        check_end.pop()
                        nodeID.pop()
                        if_end_count.pop()
                        if_start_count.pop()
                    

            for ir in n.irs:
                if self._is_instance(ir):
                    # if a return value is stored in a state variable, it's ok
                    if ir.lvalue and not isinstance(ir.lvalue, StateVariable):
                        nodes_origin[n] = [ir.lvalue]
                        bugs[ir.lvalue] = [n]
                
                elif isinstance(ir, Unary) and not isinstance(ir.rvalue, Constant) and ir.rvalue in bugs:
                    if ir.type_str == "!":
                        bugs_f.append(ir.lvalue)
                        node = bugs[ir.rvalue][0]
                        nodes_origin[node] += [ir.lvalue]
                        bugs[ir.lvalue] = bugs[ir.rvalue] + [n]
                
                elif isinstance(ir, Assignment) and not isinstance(ir.rvalue, Constant) and ir.rvalue in bugs:
                    node = bugs[ir.rvalue][0]
                    nodes_origin[node] += [ir.lvalue]
                    bugs[ir.lvalue] = bugs[ir.rvalue] + [n]

                elif isinstance(ir, Unpack) and ir.tuple in bugs:
                    node = bugs[ir.tuple][0]
                    nodes_origin[node] += [ir.lvalue]
                    bugs[ir.lvalue] = bugs[ir.tuple] + [n]
                
                elif isinstance(ir, Binary):
                    index = 0
                    for read in ir.read:
                        index += 1
                        if not isinstance(read, Constant) and read in bugs:
                            if (ir.type != BinaryType.OROR) or (read not in bugs_f):
                                node = bugs[read][0]
                                nodes_origin[node] += [ir.lvalue]
                                if n not in bugs[read]:
                                    bugs[ir.lvalue] = bugs[read] + [n]
                            if (ir.type == BinaryType.EQUAL) and (ir.read[index%2].name == "False"):
                                bugs_f.append(read)
                                node = bugs[read][0]
                                nodes_origin[node] += [ir.lvalue]
                                if n not in bugs[read]:
                                    bugs[ir.lvalue] = bugs[read] + [n]
                       
                            
                elif (  isinstance(ir, SolidityCall)
                    and ir.function.name in ["require(bool)", "require(bool,string)", "assert(bool)"]
                    ):
                    if not isinstance(ir.read[0], Constant) and ir.read[0] in bugs:
                        node = bugs[ir.read[0]][0]
                        if node in nodes_origin:
                            nodes_origin.pop(node)
                
                elif isinstance(ir, Condition) and not isinstance(ir.value, Constant) and ir.value in bugs:
                    id += 1
                    cond_bug_node.append(bugs[ir.value][0]) 
                    nodeID.append(n.node_id)
                    if_start_count.append(1) 
                    if_end_count.append(0)
                    if ir.value in bugs_f:
                        check_node.append(n.son_false.node_id)
                        check_end.append(-1)
                    else:
                        check_node.append(n.son_true.node_id)
                        check_end.append(n.son_false.node_id)

        return [node for node in nodes_origin]

    def _detect(self):
        """Detect high level calls which return a value that are never used"""
        results = []
        for c in self.compilation_unit.contracts:
            for f in c.functions + c.modifiers:
                if f.contract_declarer != c:
                    continue

                unused_return = self.detect_unused_return_values(f)

                if unused_return:
                    info = [f, " ignores return value by\n "]

                    for node in unused_return:
                        info += ["\t- ", node, "\n"]
                    
                    res = self.generate_result(info)
                    results.append(res)

        return results
