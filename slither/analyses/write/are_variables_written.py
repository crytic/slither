"""
    Detect if all the given variables are written in all the paths of the function
"""
from collections import defaultdict
from typing import Dict, Tuple, Set, List, Optional

from slither.core.cfg.node import NodeType, Node
from slither.core.declarations import SolidityFunction
from slither.core.variables.variable import Variable
from slither.slithir.operations import (
    Index,
    Member,
    OperationWithLValue,
    SolidityCall,
    Length,
    Balance,
)
from slither.slithir.variables import ReferenceVariable, TemporaryVariable


class State:
    def __init__(self):
        # Map node -> list of variables set
        # Were each variables set represents a configuration of a path
        # If two paths lead to the exact same set of variables written, we dont need to explore both
        # We need to keep different set per path, because we want to capture stuff like
        # if (..){
        #    v = 10
        # }
        # Here in the endIF node, v can be written, or can be not written. If we were merging the paths
        # We would lose this information
        # In other words, in each in the list represents a set of path that has the same outcome
        self.nodes: Dict[Node, List[Set[Variable]]] = defaultdict(list)


def _visit(
    node: Node, state: State, variables_written: Set[Variable], variables_to_write: List[Variable]
):
    """
    Explore all the nodes to look for values not written when the node's function return
    Fixpoint reaches if no new written variables are found

    :param node:
    :param state:
    :param variables_to_write:
    :return:
    """

    refs = {}
    variables_written = set(variables_written)
    for ir in node.irs:
        if isinstance(ir, SolidityCall):
            # TODO convert the revert to a THROW node
            if ir.function in [SolidityFunction("revert(string)"), SolidityFunction("revert()")]:
                return []

        if not isinstance(ir, OperationWithLValue):
            continue
        if isinstance(ir, (Index, Member)):
            refs[ir.lvalue] = ir.variable_left
        if isinstance(ir, (Length, Balance)):
            refs[ir.lvalue] = ir.value

        if ir.lvalue and not isinstance(ir.lvalue, (TemporaryVariable, ReferenceVariable)):
            variables_written.add(ir.lvalue)

        lvalue = ir.lvalue
        while isinstance(lvalue, ReferenceVariable):
            if lvalue not in refs:
                break
            if refs[lvalue] and not isinstance(
                refs[lvalue], (TemporaryVariable, ReferenceVariable)
            ):
                variables_written.add(refs[lvalue])
            lvalue = refs[lvalue]

    ret = []
    if not node.sons and node.type not in [NodeType.THROW, NodeType.RETURN]:
        ret += [v for v in variables_to_write if v not in variables_written]

    # Explore sons if
    # - Before is none: its the first time we explored the node
    # - variables_written is not before: it means that this path has a configuration of set variables
    # that we haven't seen yet
    before = state.nodes[node] if node in state.nodes else None
    if before is None or variables_written not in before:
        state.nodes[node].append(variables_written)
        for son in node.sons:
            ret += _visit(son, state, variables_written, variables_to_write)
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
    return list(set(_visit(function.entry_point, State(), set(), variables_to_write)))
