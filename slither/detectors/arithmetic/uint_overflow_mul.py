from collections import defaultdict
from slither.core.solidity_types.elementary_type import ElementaryType, Uint
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.slithir.operations import Binary, Assignment, BinaryType, Index, TypeConversion, LibraryCall, lvalue
from slither.slithir.variables import Constant, ReferenceVariable, TemporaryVariable
from slither.detectors.arithmetic.temp_and_reference_variables import Handle_TmpandRefer


def is_mul(ir):
    if isinstance(ir, Binary):
        if ir.type == BinaryType.MULTIPLICATION:
            return True
    return False

def is_div(ir):
    if isinstance(ir, Binary):
        if ir.type == BinaryType.DIVISION:
            return True
    if isinstance(ir, LibraryCall):
        if ir.function.name.lower() in [
            "div",
            "safediv",
        ]:
            if len(ir.arguments) == 2:
                if ir.lvalue:
                    return True
    return False


def is_equal_or_not_equal(ir):
    if isinstance(ir, Binary):
        if ir.type in (BinaryType.EQUAL, BinaryType.NOT_EQUAL):
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


def detect_overflow(nodes):
    results = defaultdict(list)
    arguments = defaultdict(list)
    tmps = Handle_TmpandRefer()
    safe_nodes = []
    unuse_nodes = []
    is_constant = []

    for node in nodes:
        for ir in node.irs:
            temp_vars = tmps.temp

            #a[i]
            if isinstance(ir, Index):
                tmps.handle_index(ir)

            #uint(a)
            elif isinstance(ir, TypeConversion):
                tmps.handle_conversion(ir)

            #a = tmp, c = a
            elif isinstance(ir, Assignment):
                if not isinstance(ir.lvalue.type, ElementaryType) or (ir.lvalue.type.name not in Uint):
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
            
            #(tmp|var) = (tmp|ref|var) * (tmp|ref|var)
            elif is_mul(ir):
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
                
                arguments[left] += [node]
                arguments[right] += [node]

                res = ir.lvalue
                if isinstance(res, ReferenceVariable) and (res in temp_vars):
                    res = temp_vars[res]
                if res in arguments:
                    arguments.pop(res)

                if res in results:
                    if results[res][0] not in unuse_nodes:
                        unuse_nodes += [ results[res][0] ]
                results[res] = [node]
                
            #tmp = c/a
            elif is_div(ir):
                if isinstance(ir, LibraryCall):
                    (left, right) = ir.arguments
                else:
                    (left, right) = ir.read
                if (isinstance(left, Constant)) or (isinstance(right, Constant)):
                    continue

                if isinstance(left, (ReferenceVariable, TemporaryVariable)) and (left in temp_vars):
                    left = temp_vars[left]
                    if len(left) == 1:
                        left = left[0]

                if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in temp_vars):
                    right = temp_vars[right]
                    if len(right) == 1:
                        right = right[0]

                if (left in results) and (right in arguments):
                    if results[left][0] in arguments[right]:
                        tmtemp_varsps[ir.lvalue] = (left, right)

            #tmp == b  or  tmp != b
            #b == tmp  or  b != tmp
            # check => right != b
            elif is_equal_or_not_equal(ir):
                (left, right) = ir.read
                if isinstance(left, Constant) or isinstance(right, Constant):
                    continue

                res = None
                pos = 0
                if isinstance(left, TemporaryVariable):
                    if (left in temp_vars) and (len(temp_vars[left]) == 2):
                        (r, a) = temp_vars[left]
                        if (r in results) and (a in arguments):
                            if isinstance(right, Constant):
                                right = right.name
                            if isinstance(right, (ReferenceVariable, TemporaryVariable)) and (right in temp_vars):
                                right = temp_vars[right]

                            if a == right:
                                continue
                            res = r
                            pos += 1

                        else:
                            left = temp_vars[left]

                if isinstance(right, TemporaryVariable):
                    if (right in temp_vars) and (len(temp_vars[right]) == 2):
                        (r, a) = temp_vars[right]
                        if (r in results) and (a in arguments):
                            if isinstance (left, Constant):
                                left = left.name
                            if isinstance(left, (ReferenceVariable, TemporaryVariable)) and (left in temp_vars):
                                left = temp_vars[left]

                            if a == left:
                                continue
                            res = r
                            pos += 2

                        else:
                            right = temp_vars[right]


                if (res == None) and (pos >= 3):
                    continue

                if (pos == 1) and (right in arguments):
                    res_nodes = results[res]
                    if res_nodes[0] in arguments[right]:
                        safe_nodes += [res_nodes[0]]
                        results.pop(res)

                elif (pos == 2) and (left in arguments):
                    res_nodes = results[res]
                    if res_nodes[0] in arguments[left]:
                        safe_nodes += [res_nodes[0]]
                        results.pop(res)

            elif  isinstance(ir, Binary):
                if ir.type in [
                    BinaryType.POWER,
                    BinaryType.ADDITION,
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


class UintOverfloMUL(AbstractDetector):
    """
    Documentation
    """

    ARGUMENT = (
        "multiplication-uint-overflow"  # slither will launch the detector with slither.py --detect mydetector
    )
    HELP = "unsigned_integer_overflow_mul"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.HIGH

    # region wiki
    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#unsigned-integer-overflow-mul"
    WIKI_TITLE = "Unsigned Integer Overflow"
    WIKI_DESCRIPTION = "There are also integer overflow and underflow in Ethereum, and it will not throw an exception when overflow and underflow occur. If the overflow (underflow) result is related to the amount of money, it may cause serious economic loss, so developers need to deal with integer overflow (underflow) manually. "
    WIKI_EXPLOIT_SCENARIO = """
```solidity
contract Overflow {
    function mul(uint value) public returns (bool){
    //There are also integer overflow and underflow in Ethereum, and it will not throw an exception when overflow and underflow occur. If the overflow (underflow) result is related to the amount of money, it may cause serious economic loss, so developers need to deal with integer overflow (underflow) manually. The common method is to use the SafeMath library for integer operation, or you can manually check the result after integer operation.
        sellerBalance *= value; 
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
