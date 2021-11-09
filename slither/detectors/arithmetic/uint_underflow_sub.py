from collections import defaultdict
from slither.core.solidity_types.elementary_type import ElementaryType, Uint
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, Assignment, BinaryType, Index, TypeConversion, lvalue
from slither.slithir.variables import Constant, ReferenceVariable, TemporaryVariable
from slither.detectors.arithmetic.temp_and_reference_variables import Handle_TmpandRefer


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
    tmps = Handle_TmpandRefer()
    is_constant = []
    
    for node in nodes:
        for ir in node.irs:
            temp_vars = tmps.temp

            if isinstance(ir, Index):
                tmps.handle_index(ir)

            elif isinstance(ir, TypeConversion):
                tmps.handle_conversion(ir)

            elif isinstance(ir, Assignment):
                if not isinstance(ir.rvalue, Constant):
                    right = ir.rvalue
                    if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in temp_vars):
                        right = temp_vars[right]
                        if len(right) == 1:
                            right = right[0]
            
                    if (right in bigs) or (right in smalls):
                        if right in bigs:
                            assign_value(1, ir.lvalue, right, node, bigs[right], bigs, smalls, temp_vars)
                        if right in smalls:
                            assign_value(2, ir.lvalue, right, node, smalls[right], bigs, smalls, temp_vars)
                    else:
                        delete_changed_value(ir.lvalue, bigs, smalls, temp_vars)
                else:
                    delete_changed_value(ir.lvalue, bigs, smalls, temp_vars)

            # tmp = a - b
            # a = a - b
            elif is_sub(ir):
                (left, right) = ir.read
                if (isinstance(left, Constant)) or (isinstance(right, Constant)):
                    is_constant += [ir.lvalue]
                    continue
                if (left in is_constant) or (right in is_constant):
                    is_constant += [ir.lvalue]
                    continue

                if isinstance(left, (ReferenceVariable, TemporaryVariable)) and (left in temp_vars):
                    left = temp_vars[left]
                    if len(left) == 1:
                        left = left[0]

                if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in temp_vars):
                    right = temp_vars[right]
                    if len(right) == 1:
                        right = right[0]

                flag = isnt_exited_bug(left, right, bigs, smalls)

                if flag == False:
                    f_results += [node]
                delete_changed_value(ir.lvalue, bigs, smalls, temp_vars)

            elif  isinstance(ir, Binary):
                if ir.type in [
                    BinaryType.POWER,
                    BinaryType.ADDITION,
                    BinaryType.MODULO,
                    BinaryType.MULTIPLICATION,
                    BinaryType.DIVISION,
                ]:
                    (left, right) = ir.read
                    if (isinstance(left, Constant)) or (isinstance(right, Constant)):
                        is_constant += [ir.lvalue]
                        continue
                    if (left in is_constant) or (right in is_constant):
                        is_constant += [ir.lvalue]
                        continue

            # a >= b
            elif is_greater_equal(ir):
                log_compared_variable(node, ir, bigs, smalls, temp_vars)

            # a <= b
            elif is_less_equal(ir):
                log_compared_variable(node, ir, smalls, bigs, temp_vars)

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
