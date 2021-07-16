from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, Assignment, BinaryType, Index
from slither.slithir.variables import Constant, ReferenceVariable


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


def is_rvalue_exited(node, ir, first_nodes, second_nodes, first_refers, second_refers, refers):
    if isinstance(ir.lvalue, ReferenceVariable):
        (var, index) = refers[ir.lvalue]
        if (var, index) in first_refers:
            first_refers.pop((var, index))
        if (var, index) in second_refers:
            second_refers.pop((var, index))
        first_refers[(var, index)] = first_nodes[ir.rvalue] + [node]

    elif (ir.lvalue in first_nodes) or (ir.lvalue in second_nodes):
        if ir.lvalue in first_nodes:
            first_nodes.pop(ir.lvalue)
        if ir.lvalue in second_nodes:
            second_nodes.pop(ir.lvalue)
        first_nodes[ir.lvalue] = first_nodes[ir.rvalue] + [node]

    else:
        first_nodes[ir.lvalue] = first_nodes[ir.rvalue] + [node]


def is_rvalue_exited_and_right_reference(
    node, ir, first_nodes, second_nodes, first_refers, second_refers, refers
):
    (v1, i1) = refers[ir.rvalue]
    if isinstance(ir.lvalue, ReferenceVariable):
        (v2, i2) = refers[ir.lvalue]
        if (v2, i2) in first_refers:
            first_refers.pop((v2, i2))
        if (v2, i2) in second_refers:
            second_refers.pop((v2, i2))
        first_refers[(v2, i2)] = first_refers[(v1, i1)] + [node]

    elif (ir.lvalue in first_nodes) or (ir.lvalue in second_nodes):
        if ir.lvalue in first_nodes:
            first_nodes.pop(ir.lvalue)
        if ir.lvalue in second_nodes:
            second_nodes.pop(ir.lvalue)
        first_nodes[ir.lvalue] = first_refers[(v1, i1)] + [node]

    else:
        first_nodes[ir.lvalue] = first_refers[(v1, i1)] + [node]


def log_compared_variable(node, ir, first_nodes, second_nodes, first_refers, second_refers, refers):
    (first, second) = ir.read
    if (isinstance(first, Constant)) or (isinstance(second, Constant)):
        return

    if isinstance(first, ReferenceVariable):
        (var, index) = refers[first]
        first_refers[(var, index)] += [node]
    else:
        first_nodes[first] += [node]

    if isinstance(second, ReferenceVariable):
        (var, index) = refers[second]
        second_refers[(var, index)] += [node]
    else:
        second_nodes[second] += [node]


def delete_changed_value(ir, bigs, smalls, big_nodes, small_nodes, refers):
    if isinstance(ir.lvalue, ReferenceVariable):
        (var, index) = refers[ir.lvalue]
        if (var, index) in big_nodes:
            big_nodes.pop(var, index)
        if (var, index) in small_nodes:
            small_nodes.pop(var, index)
    else:
        if ir.lvalue in bigs:
            bigs.pop(ir.lvalue)
        if ir.lvalue in smalls:
            smalls.pop(ir.lvalue)


def is_exited_bug(left, right, left_nodes, rights_nodes):
    if (left in left_nodes) and (right in rights_nodes):
        for i in left_nodes[left]:
            if i in rights_nodes[right]:
                return True
    return False


def detect_underflow(to_explore):
    f_results = []
    explored = set()
    bigs = defaultdict(list)
    smalls = defaultdict(list)
    bigs_refers = defaultdict(list)
    smalls_refers = defaultdict(list)
    refers = defaultdict(list)

    while to_explore:
        node = to_explore.pop()

        if node in explored:
            continue
        else:
            explored.add(node)
            for son in node.sons:
                to_explore.add(son)

        for ir in node.irs:
            if isinstance(ir, Assignment):
                if not isinstance(ir.rvalue, Constant):
                    if isinstance(ir.rvalue, ReferenceVariable):
                        (var, index) = refers[ir.rvalue]
                        if ((var, index) in bigs_refers) or ((var, index) in smalls_refers):
                            if (var, index) in bigs_refers:
                                is_rvalue_exited_and_right_reference(
                                    node, ir, bigs, smalls, bigs_refers, smalls_refers, refers
                                )
                            if (var, index) in smalls_refers:
                                is_rvalue_exited_and_right_reference(
                                    node, ir, smalls, bigs, smalls_refers, bigs_refers, refers
                                )
                        else:
                            delete_changed_value(
                                ir, bigs, smalls, bigs_refers, smalls_refers, refers
                            )

                    elif (ir.rvalue in bigs) or (ir.rvalue in smalls):
                        if ir.rvalue in bigs:
                            is_rvalue_exited(
                                node, ir, bigs, smalls, bigs_refers, smalls_refers, refers
                            )
                        if ir.rvalue in smalls:
                            is_rvalue_exited(
                                node, ir, smalls, bigs, bigs_refers, smalls_refers, refers
                            )

                    else:
                        delete_changed_value(ir, bigs, smalls, bigs_refers, smalls_refers, refers)
                else:
                    delete_changed_value(ir, bigs, smalls, bigs_refers, smalls_refers, refers)

            # tmp = a - b
            if is_sub(ir):
                (left, right) = ir.read
                if (isinstance(left, Constant)) or (isinstance(right, Constant)):
                    continue
                flag = False
                if isinstance(left, ReferenceVariable):
                    (v1, i1) = refers[left]
                    if isinstance(right, ReferenceVariable):
                        (v2, i2) = refers[right]
                        flag = is_exited_bug((v1, i1), (v2, i2), bigs_refers, smalls_refers)
                    else:
                        flag = is_exited_bug((v1, i1), right, bigs_refers, smalls)
                else:
                    if isinstance(right, ReferenceVariable):
                        (v2, i2) = refers[right]
                        flag = is_exited_bug(right, (v2, i2), bigs, smalls_refers)
                    else:
                        flag = is_exited_bug(left, right, bigs, smalls)

                if flag == False:
                    f_results += [node]
                delete_changed_value(ir, bigs, smalls, bigs_refers, smalls_refers, refers)

            # a >= b
            if is_greater_equal(ir):
                log_compared_variable(node, ir, bigs, smalls, bigs_refers, smalls_refers, refers)

            # a <= b
            if is_less_equal(ir):
                log_compared_variable(node, ir, smalls, bigs, smalls_refers, bigs_refers, refers)

            if isinstance(ir, Index):
                (var, index) = ir.read
                refers[ir.lvalue] = [var, index]

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

                f_results = detect_underflow({f.entry_point})

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
