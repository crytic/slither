from collections import defaultdict
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, Assignment, BinaryType, Index
from slither.slithir.variables import Constant, ReferenceVariable


def is_add(ir):
    if isinstance(ir, Binary):
        if ir.type == BinaryType.ADDITION:
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


def delete_changed_value(ir, results, arguments, result_refers, argument_refers, refers):
    if isinstance(ir.lvalue, ReferenceVariable):
        (var, index) = refers[ir.lvalue]
        if (var, index) in result_refers:
            result_refers.pop((var, index))
        if (var, index) in argument_refers:
            argument_refers.pop((var, index))
    else:
        if ir.lvalue in results:
            results.pop(ir.lvalue)
        if ir.lvalue in arguments:
            arguments.pop(ir.lvalue)


def log_unused_nodes(nodes, unuse_nodes):
    node_top = nodes.pop()
    if node_top not in unuse_nodes:
        unuse_nodes += [node_top]


def assign_value(
    argument_pos,
    node,
    left_value,
    assign_node,
    first_nodes,
    second_nodes,
    first_refers,
    second_refers,
    refers,
    unuse_nodes,
):
    if isinstance(left_value, ReferenceVariable):
        (var, index) = refers[left_value]
        if (var, index) in first_refers:
            if argument_pos == 1:
                log_unused_nodes(first_refers[(var, index)], unuse_nodes)
            first_refers.pop((var, index))

        if (var, index) in second_refers:
            if argument_pos == 2:
                log_unused_nodes(second_refers[(var, index)], unuse_nodes)
            second_refers.pop((var, index))

        if node in assign_node:
            first_refers[(var, index)] = assign_node
        else:
            first_refers[(var, index)] = assign_node + [node]

    else:
        if left_value in first_nodes:
            if argument_pos == 1:
                log_unused_nodes(first_nodes[left_value], unuse_nodes)
            first_nodes.pop(left_value)

        if left_value in second_nodes:
            if argument_pos == 2:
                log_unused_nodes(second_nodes[left_value], unuse_nodes)
            second_nodes.pop(left_value)

        if node in assign_node:
            first_nodes[left_value] = assign_node
        else:
            first_nodes[left_value] = assign_node + [node]


def has_been_judged_or_not(left, right, left_args, right_args):
    if (left in left_args) and (right in right_args):
        for i in left_args[left]:
            if i in right_args[right]:
                return True
    return False


def save_result_to_safe_node(result_nodes, argument_nodes, safe_nodes):
    for r in result_nodes:
        if r in argument_nodes:
            safe_nodes += [n for n in result_nodes if n not in safe_nodes]
            break


def check_condition(
    res, arg, results, arguments, result_refers, argument_refers, refers, safe_nodes
):
    if (isinstance(res, Constant)) or (isinstance(arg, Constant)):
        return

    if isinstance(res, ReferenceVariable):
        (v1, i1) = refers[res]
        if isinstance(arg, ReferenceVariable):
            (v2, i2) = refers[arg]
            if ((v1, i1) in result_refers) and ((v2, i2) in argument_refers):
                save_result_to_safe_node(
                    result_refers[(v1, i1)], argument_refers[(v2, i2)], safe_nodes
                )
        else:
            if ((v1, i1) in result_refers) and (arg in arguments):
                save_result_to_safe_node(result_refers[(v1, i1)], arguments[arg], safe_nodes)
    else:
        if isinstance(arg, ReferenceVariable):
            (v2, i2) = refers[arg]
            if (res in results) and ((v2, i2) in argument_refers):
                save_result_to_safe_node(results[res], argument_refers[(v2, i2)], safe_nodes)
        else:
            if (res in results) and (arg in arguments):
                save_result_to_safe_node(results[res], arguments[arg], safe_nodes)


def save_to_fRsults(results, safe_nodes, unuse_nodes):
    for key in results:
        flag = False
        for res_node in results[key]:
            if res_node in safe_nodes:
                safe_nodes += [n for n in results[key] if n not in safe_nodes]
                flag = True
                break
        if flag == False:
            unuse_nodes += [n for n in results[key] if n not in unuse_nodes]


def detect_overflow(to_explore):
    f_results = []
    explored = set()
    results = defaultdict(list)
    arguments = defaultdict(list)
    result_refers = defaultdict(list)
    argument_refers = defaultdict(list)
    refers = defaultdict(list)
    unuse_nodes = []
    safe_nodes = []

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
                        if ((var, index) in result_refers) and ((var, index) in argument_refers):
                            if (var, index) in result_refers:
                                assign_value(
                                    2,
                                    node,
                                    ir.lvalue,
                                    result_refers[(var, index)],
                                    results,
                                    arguments,
                                    result_refers,
                                    argument_refers,
                                    refers,
                                    unuse_nodes,
                                )
                            if (var, index) in argument_refers:
                                assign_value(
                                    1,
                                    node,
                                    ir.lvalue,
                                    argument_refers[(var, index)],
                                    arguments,
                                    results,
                                    argument_refers,
                                    result_refers,
                                    refers,
                                    unuse_nodes,
                                )
                        else:
                            delete_changed_value(
                                ir, results, arguments, result_refers, argument_refers, refers
                            )

                    elif (ir.rvalue in results) or (ir.rvalue in arguments):
                        if ir.rvalue in results:
                            assign_value(
                                2,
                                node,
                                ir.lvalue,
                                results[ir.rvalue],
                                results,
                                arguments,
                                result_refers,
                                argument_refers,
                                refers,
                                unuse_nodes,
                            )
                        if ir.rvalue in arguments:
                            assign_value(
                                1,
                                node,
                                ir.lvalue,
                                arguments[ir.rvalue],
                                arguments,
                                results,
                                argument_refers,
                                result_refers,
                                refers,
                                unuse_nodes,
                            )

                    else:
                        delete_changed_value(
                            ir, results, arguments, result_refers, argument_refers, refers
                        )

                else:
                    delete_changed_value(
                        ir, results, arguments, result_refers, argument_refers, refers
                    )

            # tmp = a + b
            if is_add(ir):
                (left, right) = ir.read
                if (isinstance(left, Constant)) or (isinstance(right, Constant)):
                    continue

                flag = False
                if isinstance(left, ReferenceVariable):
                    if isinstance(right, ReferenceVariable):
                        flag = has_been_judged_or_not(
                            refers[left], refers[right], argument_refers, argument_refers
                        )
                    else:
                        flag = has_been_judged_or_not(
                            refers[left], right, argument_refers, arguments
                        )
                else:
                    if isinstance(right, ReferenceVariable):
                        flag = has_been_judged_or_not(
                            left, refers[right], arguments, argument_refers
                        )
                    else:
                        flag = has_been_judged_or_not(left, right, arguments, arguments)

                if flag == False:
                    if isinstance(ir.lvalue, ReferenceVariable):
                        (var, index) = refers[ir.lvalue]
                        if (var, index) in result_refers:
                            node_top = result_refers[(var, index)].pop()
                            if node_top not in unuse_nodes:
                                unuse_nodes += [node_top]
                        result_refers[(var, index)] = [node]
                    else:
                        if ir.lvalue in results:
                            node_top = results[ir.lvalue].pop()
                            if node_top not in unuse_nodes:
                                unuse_nodes += [node_top]
                        results[ir.lvalue] = [node]

                    if isinstance(left, ReferenceVariable):
                        (var, index) = refers[left]
                        if node not in argument_refers[(var, index)]:
                            argument_refers[(var, index)] += [node]
                    else:
                        if node not in arguments[left]:
                            arguments[left] += [node]

                    if isinstance(right, ReferenceVariable):
                        (var, index) = refers[right]
                        if node not in argument_refers[(var, index)]:
                            argument_refers[(var, index)] += [node]
                    else:
                        if node not in arguments[right]:
                            arguments[right] += [node]

            # c >= a or b
            if is_greater_equal(ir):
                (res, arg) = ir.read
                check_condition(
                    res, arg, results, arguments, result_refers, argument_refers, refers, safe_nodes
                )

            # a or b <= c
            if is_less_equal(ir):
                (arg, res) = ir.read
                check_condition(
                    res, arg, results, arguments, result_refers, argument_refers, refers, safe_nodes
                )

            if isinstance(ir, Index):
                (var, index) = ir.read
                refers[ir.lvalue] = (var, index)

    save_to_fRsults(results, safe_nodes, unuse_nodes)
    save_to_fRsults(result_refers, safe_nodes, unuse_nodes)

    for unuse_node in unuse_nodes:
        if unuse_node not in safe_nodes:
            if unuse_node not in f_results:
                f_results += [unuse_node]

    return f_results


class UintOverflow(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = (
        "uint-overflow"  # slither will launch the detector with slither.py --detect mydetector
    )
    HELP = "unsigned_integer_overflow"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    # region wiki
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unsigned-integer-overflow"
    WIKI_TITLE = "Unsigned Integer Overflow"
    WIKI_DESCRIPTION = "There are also integer overflow and underflow in Ethereum, and it will not throw an exception when overflow and underflow occur. If the overflow (underflow) result is related to the amount of money, it may cause serious economic loss, so developers need to deal with integer overflow (underflow) manually. "
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Overflow {
    function add(uint value) public returns (bool){
    //There are also integer overflow and underflow in Ethereum, and it will not throw an exception when overflow and underflow occur. If the overflow (underflow) result is related to the amount of money, it may cause serious economic loss, so developers need to deal with integer overflow (underflow) manually. The common method is to use the SafeMath library for integer operation, or you can manually check the result after integer operation.
        sellerBalance += value; 
    } 
}
```
"""
    WIKI_RECOMMENDATION = "The common method is to use the SafeMath library for integer operation, or you can manually check the result after integer operation."
    # endregion wiki

    def _detect(self):
        results = []
        for c in self.contracts:
            overflow = []

            for f in c.functions_declared:
                if not f.entry_point:
                    continue

                f_results = detect_overflow({f.entry_point})

                if f_results:
                    overflow.append((f, f_results))

            if overflow:
                for (func, nodes) in overflow:
                    info = [
                        func,
                        "will maybe occured overflow\n",
                    ]

                    nodes.sort(key=lambda x: x.node_id)

                    for node in nodes:
                        info += ["\t-", node, "\n"]

                    res = self.generate_result(info)
                    results.append(res)

        return results
