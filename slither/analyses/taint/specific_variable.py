"""
    Compute taint from a specific variable

    Do not propagate taint on protected function
    Propage to state variables
    Iterate until it finding a fixpoint
"""
from slither.core.variables.variable import Variable
from slither.core.variables.state_variable import StateVariable
from slither.core.declarations.solidity_variables import SolidityVariable, SolidityVariableComposed

from slither.slithir.operations.index import Index
from slither.slithir.operations.member import Member
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.reference import ReferenceVariable

def make_key(variable):
    if isinstance(variable, Variable):
        key = 'TAINT_{}{}{}'.format(variable.contract.name,
                                    variable.name,
                                    str(type(variable)))
    else:
        assert isinstance(variable, SolidityVariable)
        key = 'TAINT_{}{}'.format(variable.name,
                                    str(type(variable)))
    return key

def _visit_node(node, visited, key):
    if node in visited:
        return

    visited = visited + [node]
    taints = node.function.slither.context[key]

    refs = {}
    for ir in node.irs:
        if not isinstance(ir, OperationWithLValue):
            continue
        if isinstance(ir, (Index, Member)):
            refs[ir.lvalue] = ir.variable_left

        if isinstance(ir, Index):
            read = [ir.variable_left]
        else:
            read = ir.read
#        print(ir)
#        print('READ {}'.format([str(v) for v in read]))
#        print('TAINT {}'.format([str(v) for v in taints]))
#        print(any(var_read in taints for var_read in read))
#        print()
        if isinstance(ir, OperationWithLValue) and any(is_tainted_from_key(var_read, key) or var_read in taints for var_read in read):
            taints += [ir.lvalue]
            ir.lvalue.context[key] = True
            lvalue = ir.lvalue
            while  isinstance(lvalue, ReferenceVariable):
                taints += [refs[lvalue]]
                lvalue = refs[lvalue]
                lvalue.context[key] = True

    taints = [v for v in taints if not isinstance(v, (TemporaryVariable, ReferenceVariable))]

    node.function.slither.context[key] = list(set(taints))

    for son in node.sons:
        _visit_node(son, visited, key)

def run_taint(slither, taint):

    key = make_key(taint)

    prev_taints = []
    slither.context[key] = [taint]
    # Loop until reaching a fixpoint
    while(set(prev_taints) != set(slither.context[key])):
        prev_taints = slither.context[key]
        for contract in slither.contracts:
            for function in contract.functions:
                # Dont propagated taint on protected functions
                if function.is_implemented and not function.is_protected():
                    slither.context[key] = list(set(slither.context[key]))
                    _visit_node(function.entry_point, [], key)

    slither.context[key] = [v for v in prev_taints if isinstance(v, (StateVariable, SolidityVariable))]

def is_tainted(variable, taint):
    """
    Args:
        variable (Variable)
        taint (Variable): Root of the taint
    """
    if not isinstance(variable, (Variable, SolidityVariable)):
        return False
    key = make_key(taint)
    return key in variable.context and variable.context[key]

def is_tainted_from_key(variable, key):
    """
    Args:
        variable (Variable)
        key (str): key
    """
    if not isinstance(variable, (Variable, SolidityVariable)):
        return False
    return key in variable.context and variable.context[key]


def get_state_variable_tainted(slither, taint):
    key = make_key(taint)
    return slither.context[key]
