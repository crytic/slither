"""
    Compute taint on state variables

    Do not propagate taint on protected function
    Compute taint from function parameters, msg.sender and msg.value
    Iterate until it finding a fixpoint

"""
from slither.core.declarations.solidity_variables import \
    SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import Index, Member, OperationWithLValue
from slither.slithir.variables import ReferenceVariable#, TemporaryVariable

from .common import iterate_over_irs
KEY = 'TAINT_ALL_VARIABLES'

def _transfer_func(ir, read, refs, taints):
    if isinstance(ir, OperationWithLValue) and any(var_read in taints for var_read in read):
        taints += [ir.lvalue]
        lvalue = ir.lvalue
        while  isinstance(lvalue, ReferenceVariable):
            taints += [refs[lvalue]]
            lvalue = refs[lvalue]
    return taints

def _visit_node(node, visited):
    if node in visited:
        return

    visited += [node]
    taints = node.function.slither.context[KEY]

    taints = iterate_over_irs(node.irs, _transfer_func, taints)

#    taints = [v for v in taints if not isinstance(v, (TemporaryVariable, ReferenceVariable))]

    node.function.slither.context[KEY] = list(set(taints))

    for son in node.sons:
        _visit_node(son, visited)


def _run_taint(slither, initial_taint):
    if KEY in slither.context:
        return

    prev_taints = []
    slither.context[KEY] = initial_taint
    # Loop until reaching a fixpoint
    while(set(prev_taints) != set(slither.context[KEY])):
        prev_taints = slither.context[KEY]
        for contract in slither.contracts:
            for function in contract.functions:
                if not function.is_implemented:
                    continue
                # Dont propagated taint on protected functions
                if not function.is_protected():
                    slither.context[KEY] = list(set(slither.context[KEY] + function.parameters))
                    _visit_node(function.entry_point, [])

    slither.context[KEY] = prev_taints # [v for v in prev_taints if isinstance(v, StateVariable)]

def run_taint(slither, initial_taint=None):
    if initial_taint is None:
        initial_taint = [SolidityVariableComposed('msg.sender')]
        initial_taint += [SolidityVariableComposed('msg.value')]
        initial_taint += [SolidityVariableComposed('msg.data')]
        initial_taint += [SolidityVariableComposed('tx.origin')]

    if KEY not in slither.context:
        _run_taint(slither, initial_taint)

def get_taint(slither, initial_taint=None):
    """
        Return the state variables tainted
    Args:
        slither:
        initial_taint (List Variable)
    Returns:
        List(StateVariable)
    """
    run_taint(slither, initial_taint)
    return slither.context[KEY]

def is_tainted(slither, variable):
    """
        Returns if the variable is tainted by inputs
    Args:
        slither
        variable (Variable)
    Returns:
        bool
    """
    if KEY not in slither.context:
        run_taint(slither)

    return variable in slither.context[KEY]
