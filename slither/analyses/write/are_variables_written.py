"""
    Detect if all the given variables are written in all the paths of the function
"""
from slither.core.cfg.node import NodeType
from slither.core.declarations import SolidityFunction
from slither.slithir.operations import (Index, Member, OperationWithLValue,
                                        SolidityCall, Length, Balance)
from slither.slithir.variables import ReferenceVariable


def _visit(node, visited, variables_written, variables_to_write):

    if node in visited:
        return []

    visited = visited + [node]

    refs = {}
    for ir in node.irs:
        if isinstance(ir, SolidityCall):
            # TODO convert the revert to a THROW node
            if ir.function in [SolidityFunction('revert(string)'),
                               SolidityFunction('revert()')]:
                return []

        if not isinstance(ir, OperationWithLValue):
            continue
        if isinstance(ir, (Index, Member)):
            refs[ir.lvalue] = ir.variable_left
        if isinstance(ir, (Length, Balance)):
            refs[ir.lvalue] = ir.value

        variables_written = variables_written + [ir.lvalue]
        lvalue = ir.lvalue
        while  isinstance(lvalue, ReferenceVariable):
            if lvalue not in refs:
                break
            variables_written = variables_written + [refs[lvalue]]
            lvalue = refs[lvalue]

    ret = []
    if not node.sons and not node.type in [NodeType.THROW, NodeType.RETURN]:
        ret += [v for v in variables_to_write if not v in variables_written]

    for son in node.sons:
        ret += _visit(son, visited, variables_written, variables_to_write)
    return ret

def are_variables_written(function, variables_to_write):
    """
        Return the list of variable that are not written at the end of the function

    Args:
        function (Function)
        variables_to_write (list Variable): variable that must be written
    Returns:
        list(Variable): List of variable that are not written (sublist of variables_to_write)
    """
    return list(set(_visit(function.entry_point, [], [], variables_to_write)))
