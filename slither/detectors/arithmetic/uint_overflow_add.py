from collections import defaultdict
from slither.core.solidity_types.elementary_type import ElementaryType, Uint
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, Assignment, BinaryType, Index, TypeConversion
from slither.slithir.variables import Constant, ReferenceVariable, TemporaryVariable
from slither.detectors.arithmetic.temp_and_reference_variables import Handle_TmpandRefer


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


def delete_changed_value(left, results, arguments, tmps, unuse_nodes):
    if isinstance(left, ReferenceVariable) and (left in tmps):
        left = tmps[left]
        if len(left) == 1:
            left = left[0]

    if left in results:
        if results[left][0] not in unuse_nodes:
            unuse_nodes += [ results[left][0] ]
        results.pop(left)

    if left in arguments:
        arguments.pop(left)


def assign_value(pos, left, right, node, assign_node, results, arguments, tmps, unuse_nodes):
    if isinstance(left, ReferenceVariable) and (left in tmps):
        left = tmps[left]
        if len(left) == 1:
            left = left[0]

    if left == right:
        return

    if left in results:
        if results[left][0] not in unuse_nodes:
            unuse_nodes += [ results[left][0] ]
        results.pop(left)
    if left in arguments:
        arguments.pop(left)

    if node not in assign_node:
        assign_node += [node]
    if pos == 1:
        results[left] = assign_node
    elif pos ==2:
        arguments[left] = assign_node


def is_exited_bug(left, right, arguments):
    nodes = []
    if (left in arguments) and (right in arguments):
        for i in arguments[left]:
            if i in arguments[right]:
                nodes += [i]
    return nodes


    

def check_condition(res, arg, results, arguments, tmps, safe_nodes):
    if (isinstance(res, Constant)) or (isinstance(arg, Constant)):
        return
    if isinstance(res, (ReferenceVariable, TemporaryVariable)) and (res in tmps):
        res = tmps[res]
        if len(res) == 1:
            res = res[0]

    if isinstance(arg, (ReferenceVariable, TemporaryVariable)) and (arg in tmps):
        arg= tmps[arg]
        if len(arg) == 1:
            arg = arg[0]

    if (res in results) and (arg in arguments):
        res_node = results[res][0]
        if (res_node in arguments[arg]) and (res_node not in safe_nodes):
            safe_nodes += [res_node]


def detect_overflow(nodes):
    results = defaultdict(list)
    arguments = defaultdict(list)
    tmps = Handle_TmpandRefer()
    unuse_nodes = []
    safe_nodes = []
    is_constant = []

    for node in nodes:
        for ir in node.irs:
            temp_vars = tmps.temp

            # a[i]
            if isinstance(ir, Index):
                tmps.handle_index(ir)

            # uint(a)
            elif isinstance(ir, TypeConversion):
                tmps.handle_conversion(ir)

            #a = tmp, c = a
            elif isinstance(ir, Assignment):
                if not isinstance(ir.lvalue.type, ElementaryType) or  (ir.lvalue.type.name not in Uint):
                    continue
                
                if not isinstance(ir.rvalue, Constant):
                    right = ir.rvalue
                    if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in temp_vars):
                        right = temp_vars[right]
                        if len(right) == 1:
                            right = right[0]
            
                    if (right in results) or (right in arguments):
                        if right in results:
                            assign_value(1, ir.lvalue, right, node, results[right], results, arguments, temp_vars, unuse_nodes)
                        if right in arguments:
                            assign_value(2, ir.lvalue, right, node, arguments[right], results, arguments, temp_vars, unuse_nodes)
                    else:
                        delete_changed_value(ir.lvalue, results, arguments, temp_vars, unuse_nodes)
                else:
                    delete_changed_value(ir.lvalue, results, arguments, temp_vars, unuse_nodes)

            # tmp = a + b
            elif is_add(ir):
                (left, right) = ir.read
                res = ir.lvalue
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
                
                exist_nodes = is_exited_bug(left, right, arguments)
                 
                flag = False
                if len(exist_nodes) > 0:
                    for i in exist_nodes:
                        if i in safe_nodes:
                            flag = True
                            break

                if flag == False:
                    if isinstance(left, (ReferenceVariable, TemporaryVariable)) and (left in temp_vars):
                        left = temp_vars[left]
                        if len(left) == 1:
                            left = left[0]
                    if node not in arguments[left]:
                        arguments[left] += [node]

                    if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in temp_vars):
                        right = temp_vars[right]
                        if len(right) == 1:
                            right = right[0]
                    if node not in arguments[right]:
                        arguments[right] += [node]

                        
                    if isinstance(res, ReferenceVariable) and (res in temp_vars):
                        res = temp_vars[res]

                    if res in arguments:
                        arguments.pop(res)

                    if res in results:
                        if results[res][0] not in unuse_nodes:
                            unuse_nodes += [ results[res][0] ]
                    results[res] = [node]

            # c >= a or b
            elif is_greater_equal(ir):
                (res, arg) = ir.read
                check_condition(res, arg, results, arguments, temp_vars, safe_nodes)

            # a or b <= c
            elif is_less_equal(ir):
                (arg, res) = ir.read
                check_condition(res, arg, results, arguments, temp_vars, safe_nodes)

            elif  isinstance(ir, Binary):
                if ir.type in [
                    BinaryType.POWER,
                    BinaryType.MULTIPLICATION,
                    BinaryType.MODULO,
                    BinaryType.SUBTRACTION,
                    BinaryType.DIVISION,
                ]:
                    (left, right) = ir.read
                    if (isinstance(left, Constant)) or (isinstance(right, Constant)):
                        is_constant += [ir.lvalue]
                        continue
                    if (left in is_constant) or (right in is_constant):
                        is_constant += [ir.lvalue]
                        continue
                
    
    f_results = []
    for key in results:
        if results[key][0] not in safe_nodes:
            if results[key][0] not in f_results:
                f_results += [results[key][0]]
    for un in unuse_nodes:
        if un not in safe_nodes:
            if un not in f_results:
                f_results += [un]

    return f_results


class UintOverflowADD(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = (
        "addition-uint-overflow"  # slither will launch the detector with slither.py --detect mydetector
    )
    HELP = "unsigned_integer_overflow_add"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    # region wiki
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unsigned-integer-overflow-add"
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

                f_results = detect_overflow(f.nodes)

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
