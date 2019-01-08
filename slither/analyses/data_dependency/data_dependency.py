"""
    Compute the data depenency between all the SSA variables
"""
from slither.core.declarations import Contract, Function
from slither.slithir.operations import Index, Member, OperationWithLValue
from slither.slithir.variables import ReferenceVariable, Constant
from slither.slithir.variables import (Constant, LocalIRVariable, StateIRVariable,
                                       ReferenceVariable, TemporaryVariable,
                                       TupleVariable)


from slither.core.declarations.solidity_variables import \
    SolidityVariableComposed

KEY_SSA = "DATA_DEPENDENCY_SSA"
KEY_NON_SSA = "DATA_DEPENDENCY"

# Only for unprotected functions
KEY_SSA_UNPROTECTED = "DATA_DEPENDENCY_SSA_UNPROTECTED"
KEY_NON_SSA_UNPROTECTED = "DATA_DEPENDENCY_UNPROTECTED"

KEY_INPUT = "DATA_DEPENDENCY_INPUT"
KEY_INPUT_SSA = "DATA_DEPENDENCY_INPUT_SSA"

def pprint_dependency(context):
    print('#### SSA ####')
    context = context.context
    for k, values in context[KEY_SSA].items():
        print('{} ({}):'.format(k, id(k)))
        for v in values:
            print('\t- {}'.format(v))

    print('#### NON SSA ####')
    for k, values in context[KEY_NON_SSA].items():
        print('{} ({}):'.format(k, hex(id(k))))
        for v in values:
            print('\t- {}'.format(v))


def is_dependent(variable, source, context, only_unprotected=False):
    '''
    Args:
        variable (Variable)
        source (Variable)
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    '''
    assert isinstance(context, (Contract, Function))
    if isinstance(variable, Constant):
        return False
    if variable == source:
        return True
    context = context.context
    if only_unprotected:
        return variable in context[KEY_NON_SSA_UNPROTECTED] and source in context[KEY_NON_SSA_UNPROTECTED][variable]
    return variable in context[KEY_NON_SSA] and source in context[KEY_NON_SSA][variable]

def is_dependent_ssa(variable, source, context, only_unprotected=False):
    '''
    Args:
        variable (Variable)
        taint (Variable)
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    '''
    assert isinstance(context, (Contract, Function))
    context = context.context
    if isinstance(variable, Constant):
        return False
    if variable == source:
        return True
    if only_unprotected:
        return variable in context[KEY_SSA_UNPROTECTED] and source in context[KEY_SSA_UNPROTECTED][variable]
    return variable in context[KEY_SSA] and source in context[KEY_SSA][variable]

GENERIC_TAINT = {SolidityVariableComposed('msg.sender'),
                 SolidityVariableComposed('msg.value'),
                 SolidityVariableComposed('msg.data'),
                 SolidityVariableComposed('tx.origin')}

def is_tainted(variable, context, slither, only_unprotected=False):
    '''
        Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    '''
    assert isinstance(context, (Contract, Function))
    taints = slither.context[KEY_INPUT]
    taints |= GENERIC_TAINT
    return variable in taints or any(is_dependent(variable, t, context, only_unprotected) for t in taints)

def is_tainted_ssa(variable, context, slither, only_unprotected=False):
    '''
    Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    '''
    assert isinstance(context, (Contract, Function))
    taints = slither.context[KEY_INPUT_SSA]
    taints |= GENERIC_TAINT
    return variable in taints or any(is_dependent_ssa(variable, t, context, only_unprotected) for t in taints)

def compute_dependency(slither):

    slither.context[KEY_INPUT] = set()
    slither.context[KEY_INPUT_SSA] = set()

    for contract in slither.contracts:
        compute_dependency_contract(contract, slither)

def compute_dependency_contract(contract, slither):
    if KEY_SSA in contract.context:
        return

    contract.context[KEY_SSA] = dict()
    contract.context[KEY_SSA_UNPROTECTED] = dict()

    for function in contract.all_functions_called:
        compute_dependency_function(function)

        propagate_function(contract, function, KEY_SSA)
        propagate_function(contract, function, KEY_SSA_UNPROTECTED)

        [slither.context[KEY_INPUT].add(p) for p in function.parameters]
        [slither.context[KEY_INPUT_SSA].add(p) for p in function.parameters_ssa]

    propagate_contract(contract, KEY_SSA, KEY_NON_SSA)
    propagate_contract(contract, KEY_SSA_UNPROTECTED, KEY_NON_SSA_UNPROTECTED)

def propagate_function(contract, function, context_key):
    # Propage data dependency
    data_depencencies = function.context[context_key]
    for (key, values) in data_depencencies.items():
        if not key in contract.context[context_key]:
            contract.context[context_key][key] = set(values)
        else:
            contract.context[context_key][key].union(values)

def propagate_contract(contract, context_key, context_key_non_ssa):
    # transitive closure
    changed = True
    while changed:
        changed = False
        # Need to create new set() as its changed during iteration
        data_depencencies = {k: set([v for v in values]) for k, values in  contract.context[context_key].items()}
        for key, items in data_depencencies.items():
            for item in items:
                if item in data_depencencies:
                    additional_items = contract.context[context_key][item]
                    for additional_item in additional_items:
                        if not additional_item in items and additional_item != key:
                            changed = True
                            contract.context[context_key][key].add(additional_item)
    contract.context[context_key_non_ssa] = convert_to_non_ssa(contract.context[context_key])

def add_dependency(lvalue, function, ir, is_protected):
    if not lvalue in function.context[KEY_SSA]:
        function.context[KEY_SSA][lvalue] = set()
        if not is_protected:
            function.context[KEY_SSA_UNPROTECTED][lvalue] = set()
    if isinstance(ir, Index):
        read = [ir.variable_left]
    else:
        read = ir.read
    [function.context[KEY_SSA][lvalue].add(v) for v in read if not isinstance(v, Constant)]
    if not is_protected:
        [function.context[KEY_SSA_UNPROTECTED][lvalue].add(v) for v in read if not isinstance(v, Constant)]


def compute_dependency_function(function):
    if KEY_SSA in function.context:
        return

    function.context[KEY_SSA] = dict()
    function.context[KEY_SSA_UNPROTECTED] = dict()

    is_protected = function.is_protected

    for node in function.nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, OperationWithLValue) and ir.lvalue:
                if isinstance(ir.lvalue, LocalIRVariable) and ir.lvalue.is_storage:
                    continue
                if isinstance(ir.lvalue, ReferenceVariable):
                    lvalue = ir.lvalue.points_to
                    if lvalue:
                        add_dependency(lvalue, function, ir, is_protected)
                add_dependency(ir.lvalue, function, ir, is_protected)

    function.context[KEY_NON_SSA] = convert_to_non_ssa(function.context[KEY_SSA])
    function.context[KEY_NON_SSA_UNPROTECTED] = convert_to_non_ssa(function.context[KEY_SSA_UNPROTECTED])

def convert_variable_to_non_ssa(v):
    if isinstance(v, (LocalIRVariable, StateIRVariable)):
        if isinstance(v, LocalIRVariable):
            function = v.function
            return function.get_local_variable_from_name(v.name)
        else:
            contract = v.contract
            return contract.get_state_variable_from_name(v.name)
    if isinstance(v, (TemporaryVariable, ReferenceVariable)):
        return next((variable for variable in v.function.slithir_variables if variable.name == v.name))
    return v

def convert_to_non_ssa(data_depencies):
    # Need to create new set() as its changed during iteration
    ret = dict()
    for (k, values) in data_depencies.items():
        var = convert_variable_to_non_ssa(k)
        if not var in ret:
            ret[var] = set()
        ret[var] = ret[var].union(set([convert_variable_to_non_ssa(v) for v in
                                       values]))

    return ret
