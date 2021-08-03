from collections import defaultdict
from slither.core.solidity_types.elementary_type import ElementaryType, Uint
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, Assignment, BinaryType, Index, TypeConversion
from slither.slithir.variables import Constant, ReferenceVariable, TemporaryVariable


def is_sub(ir):
    if isinstance(ir, Binary):
        if ir.type == BinaryType.SUBTRACTION:
            return True
    return False


def is_less_equal(ir):
    if isinstance(ir, Binary):
        if (ir.type == BinaryType.LESS_EQUAL) or (ir.type == BinaryType.LESS):
            return True
    return False


def is_greater_equal(ir):
    if isinstance(ir, Binary):
        if (ir.type == BinaryType.GREATER_EQUAL) or (ir.type == BinaryType.GREATER):
            return True
    return False


def assign_value(pos, left, right, node, assign_node, bigs, smalls, tmps):
    if isinstance(left, ReferenceVariable) and (left in tmps):
        left = tmps[left]
        if len(left) == 1:
            left = left[0]

    if left == right:
        return

    if left in bigs:
        bigs.pop(left)
    if left in smalls:
        smalls.pop(left)

    if node not in assign_node:
        assign_node += [node]
    if pos == 1:
        bigs[left] = assign_node
    elif pos ==2:
        smalls[left] = assign_node


def log_compared_variable(node, ir, first_nodes, second_nodes, tmps):
    (first, second) = ir.read
    if (isinstance(first, Constant)) or (isinstance(second, Constant)):
        return
    
    if (first.type.name not in Uint) or (second.type.name not in Uint):
        return

    if isinstance(first, (ReferenceVariable, TemporaryVariable)) and (first in tmps):
        first = tmps[first]
        if len(first) == 1:
            first = first[0]

    if isinstance(second, (ReferenceVariable, TemporaryVariable)) and (second in tmps):
        second = tmps[second]
        if len(second) == 1:
            second = second[0]

    if node not in first_nodes[first]:
        first_nodes[first] += [node]

    if node not in second_nodes[second]:
        second_nodes[second] += [node]


def delete_changed_value(left, bigs, smalls, tmps):
    if isinstance(left, ReferenceVariable) and (left in tmps):
        left = tmps[left]
        if len(left) == 1:
            left = left[0]

    if left in bigs:
        bigs.pop(left)
    if left in smalls:
        smalls.pop(left)


def isnt_exited_bug(left, right, bigs, smalls):
    if (left in bigs) and (right in smalls):
        for i in bigs[left]:
            if i in smalls[right]:
                return True
    return False


def detect_underflow(nodes):
    f_results = []
    bigs = defaultdict(list)
    smalls = defaultdict(list)
    tmps = defaultdict(list)

    for node in nodes:
        for ir in node.irs:
            if isinstance(ir, Index) and isinstance(ir.lvalue.type, ElementaryType):
                if ir.lvalue.type.name in Uint:
                    (var, index) = ir.read

                    # avoid unhashable type "Constant"
                    if isinstance(index, Constant):
                        index = index.name

                    if isinstance(index, (ReferenceVariable, TemporaryVariable)) and (index in tmps):
                        index = tmps[index]
                        if len(index) == 1:
                            index = index[0]

                    tmps[ir.lvalue] = (var, index)

            elif isinstance(ir, TypeConversion) and (ir.lvalue.type.name in Uint):
                if isinstance(ir.variable, Constant):
                    continue
                
                var = ir.variable
                only = 0

                if isinstance(var, (ReferenceVariable, TemporaryVariable)) and (var in tmps):
                        var = tmps[var]
                        if len(var) == 1:
                            var = var[0]
                        else:
                            only += 1

                if only == 0:
                    tmps[ir.lvalue] = [var]
                else:
                    tmps[ir.lvalue] = var

            if isinstance(ir, Assignment) and (ir.lvalue.type.name in Uint):
                if not isinstance(ir.rvalue, Constant):
                    right = ir.rvalue
                    if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in tmps):
                        right = tmps[right]
                        if len(right) == 1:
                            right = right[0]
            
                    if (right in bigs) or (right in smalls):
                        if right in bigs:
                            assign_value(1, ir.lvalue, right, node, bigs[right], bigs, smalls, tmps)
                        if right in smalls:
                            assign_value(2, ir.lvalue, right, node, smalls[right], bigs, smalls, tmps)
                    else:
                        delete_changed_value(ir.lvalue, bigs, smalls, tmps)
                else:
                    delete_changed_value(ir.lvalue, bigs, smalls, tmps)

            # tmp = a - b
            # a = a - b
            if is_sub(ir) and (ir.lvalue.type.name in Uint):
                (left, right) = ir.read
                if (isinstance(left, Constant)) or (isinstance(right, Constant)):
                    continue

                if isinstance(left, (ReferenceVariable, TemporaryVariable)) and (left in tmps):
                    left = tmps[left]
                    if len(left) == 1:
                        left = left[0]

                if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in tmps):
                    right = tmps[right]
                    if len(right) == 1:
                        right = right[0]

                flag = isnt_exited_bug(left, right, bigs, smalls)

                if flag == False:
                    f_results += [node]
                delete_changed_value(ir.lvalue, bigs, smalls, tmps)

            # a >= b
            if is_greater_equal(ir):
                log_compared_variable(node, ir, bigs, smalls, tmps)

            # a <= b
            if is_less_equal(ir):
                log_compared_variable(node, ir, smalls, bigs, tmps)

    return f_results


class UintUnderflow(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = (
        "uint-underflow"  # slither will launch the detector with slither.py --detect mydetector
    )
    HELP = "unsigned_integer_underflow"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    # region wiki
    WIKI = (
        "https://github.com/crytic/slither/wiki/Detector-Documentation#unsigned-integer-underflow"
    )
    WIKI_TITLE = "Unsigned Integer Underflow"
    WIKI_DESCRIPTION = "There are also integer overflow and underflow in Ethereum, and it will not throw an exception when overflow and underflow occur. If the overflow (underflow) result is related to the amount of money, it may cause serious economic loss, so developers need to deal with integer overflow (underflow) manually. "
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Overflow {
    function add(uint value) public returns (bool){
        balances[msg.sender] -= _value;
    } 
}
```
"""
    WIKI_RECOMMENDATION = "The common method is to use the SafeMath library for integer operation, or you can manually check the result after integer operation."
    # endregion wiki

    def _detect(self):
        results = []
        for c in self.contracts:
            underflow = []

            for f in c.functions_declared:
                if not f.entry_point:
                    continue

                f_results = detect_underflow(f.nodes)

                if f_results:
                    underflow.append((f, f_results))

            if underflow:
                for (func, nodes) in underflow:
                    info = [
                        func,
                        "will maybe occured underflow\n",
                    ]

                    nodes.sort(key=lambda x: x.node_id)

                    for node in nodes:
                        info += ["\t-", node, "\n"]

                    res = self.generate_result(info)
                    results.append(res)

        return results
