"""
    Compute the data depenency between all the SSA variables
"""
from collections import defaultdict
from slither.core.declarations import (Contract, Enum, Function,
                                       SolidityFunction, SolidityVariable,
                                       SolidityVariableComposed, Structure)
from slither.core.solidity_types import UserDefinedType
from slither.slithir.operations import Index, OperationWithLValue, InternalCall, PhiMemberMust, PhiMemberMay, \
    AccessMember
from slither.slithir.utils.ssa import last_name
from slither.slithir.variables import (Constant, LocalIRVariable,
                                       IndexVariable, IndexVariableSSA,
                                       StateIRVariable, MemberVariable, MemberVariableSSA,
                                       TemporaryVariableSSA, TupleVariableSSA)
from slither.core.solidity_types.type import Type


###################################################################################
###################################################################################
# region User APIs
###################################################################################
###################################################################################

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

def is_tainted(variable, context, only_unprotected=False, ignore_generic_taint=False):
    '''
        Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    '''
    assert isinstance(context, (Contract, Function))
    assert isinstance(only_unprotected, bool)
    if isinstance(variable, Constant):
        return False
    slither = context.slither
    taints = slither.context[KEY_INPUT]
    if not ignore_generic_taint:
        taints |= GENERIC_TAINT
    return variable in taints or any(is_dependent(variable, t, context, only_unprotected) for t in taints)

def is_tainted_ssa(variable, context, only_unprotected=False, ignore_generic_taint=False):
    '''
    Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        bool
    '''
    assert isinstance(context, (Contract, Function))
    assert isinstance(only_unprotected, bool)
    if isinstance(variable, Constant):
        return False
    slither = context.slither
    taints = slither.context[KEY_INPUT_SSA]
    if not ignore_generic_taint:
        taints |= GENERIC_TAINT
    return variable in taints or any(is_dependent_ssa(variable, t, context, only_unprotected) for t in taints)


def get_dependencies(variable, context, only_unprotected=False):
    '''
    Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        list(Variable)
    '''
    if isinstance(variable, list):
        return _get_dependencies_from_nested(variable, context, only_unprotected)
    assert isinstance(context, (Contract, Function))
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_NON_SSA].get(variable, [])
    return context.context[KEY_NON_SSA_UNPROTECTED].get(variable, [])


def _get_dependencies_from_nested(variables, context, only_unprotected=False):

    if only_unprotected:
        context = context.context[KEY_NON_SSA]
    else:
        context = context.context[KEY_NON_SSA_UNPROTECTED]

    print(f'Try {[str(x) for x in variables]}')
    next_level = [variables[0]]
    variables = variables[1:]
    print(f'Try {[str(x) for x in variables]}')
    while variables:
        next_next = []
        variable = variables[0]
        variables = variables[1:]
        for next in next_level:
            key = (next, variable)
            print(f'First key {next}.{variable}')
            if key in context:
                next_next += context[key]
            else:
                print(f'Missing {next}.{variable}')
        next_level = next_next


    return next_level


# endregion
###################################################################################
###################################################################################
# region Module constants
###################################################################################
###################################################################################

KEY_SSA = "DATA_DEPENDENCY_SSA"
KEY_NON_SSA = "DATA_DEPENDENCY"
#
# KEY_SSA_MEMBERS = "DATA_DEPENDENCY_SSA_MEMBERS"
# KEY_NON_SSA_MEMBERS = "DATA_DEPENDENCY_MEMBERS"

# Only for unprotected functions
KEY_SSA_UNPROTECTED = "DATA_DEPENDENCY_SSA_UNPROTECTED"
KEY_NON_SSA_UNPROTECTED = "DATA_DEPENDENCY_UNPROTECTED"

# KEY_SSA_MEMBERS_UNPROTECTED = "DATA_DEPENDENCY_SSA_UNPROTECTED"
# KEY_NON_SSA_MEMBERS_UNPROTECTED = "DATA_DEPENDENCY_UNPROTECTED"

KEY_INPUT = "DATA_DEPENDENCY_INPUT"
KEY_INPUT_SSA = "DATA_DEPENDENCY_INPUT_SSA"


# endregion
###################################################################################
###################################################################################
# region Debug
###################################################################################
###################################################################################

def pprint_dependency(context):
    print('#### SSA ####')
    context = context.context
    if KEY_SSA not in context:
        return
    for k, values in context[KEY_SSA].items():
        if isinstance(k, tuple):
            print('{}.{} ({}):'.format(k[0], k[1], id(k)))
        else:
            print('{} ({}):'.format(k, id(k)))
        for v in values:
            if isinstance(v, tuple):
                print('\t- {}.{}'.format(v[0], v[1]))
            else:
                print('\t- {}'.format(v))

    print('#### NON SSA ####')
    if KEY_NON_SSA not in context:
        return
    for k, values in context[KEY_NON_SSA].items():
        if isinstance(k, tuple):
            print('{}.{} ({}):'.format(k[0], k[1], id(k)))
        else:
            print('{} ({}):'.format(k, id(k)))
        for v in values:
            if isinstance(v, tuple):
                print('\t- {}.{}'.format(v[0], v[1]))
            else:
                print('\t- {}'.format(v))

# endregion
###################################################################################
###################################################################################
# region Analyses
###################################################################################
###################################################################################

def compute_dependency(slither):

    slither.context[KEY_INPUT] = set()
    slither.context[KEY_INPUT_SSA] = set()

    for contract in slither.contracts:
        compute_dependency_contract(contract, slither)

def compute_dependency_contract(contract, slither):
    if KEY_SSA in contract.context:
        return

    contract.context[KEY_SSA] = defaultdict(set)
    contract.context[KEY_SSA_UNPROTECTED] = defaultdict(set)

    for function in contract.all_functions_called:
        compute_dependency_function(function)

        # print(f'\n\n\n\n\n\nFunction done')
        # pprint_dependency(function)

        propagate_function(contract, function, KEY_SSA, KEY_NON_SSA)
        propagate_function(contract,
                           function,
                           KEY_SSA_UNPROTECTED,
                           KEY_NON_SSA_UNPROTECTED)

        if function.visibility in ['public', 'external']:
            [slither.context[KEY_INPUT].add(p) for p in function.parameters]
            [slither.context[KEY_INPUT_SSA].add(p) for p in function.parameters_ssa]
        print('############ after propage')
        pprint_dependency(function)
        print('################################################')


    propagate_contract(contract, KEY_SSA, KEY_NON_SSA)
    propagate_contract(contract, KEY_SSA_UNPROTECTED, KEY_NON_SSA_UNPROTECTED)

def propagate_function(contract, function, context_key, context_key_non_ssa):
    #transitive_close_dependencies(function, context_key, context_key_non_ssa)
    # Propage data dependency
    data_depencencies = function.context[context_key]

    for (key, values) in data_depencencies.items():
        if not key in contract.context[context_key]:
            contract.context[context_key][key] = set(values)
        else:
            contract.context[context_key][key] = contract.context[context_key][key].union(values)

def transitive_close_dependencies(context, context_key, context_key_non_ssa):
    # transitive closure
    changed = True
    while changed:
        changed = False
        # Need to create new set() as its changed during iteration
        data_depencencies = {k: set([v for v in values]) for k, values in context.context[context_key].items()}
        for key, items in data_depencencies.items():
            for item in items:
                if item in data_depencencies:
                    additional_items = context.context[context_key][item]
                    for additional_item in additional_items:
                        if not additional_item in items and additional_item != key:
                            changed = True
                            context.context[context_key][key].add(additional_item)
    context.context[context_key_non_ssa] = convert_to_non_ssa(context.context[context_key])

def transitive_close_node_dependencies(node, context_key, context_key_non_ssa):
    # transitive closure
    changed = True
    updated_dependencies = False
    while changed:
        changed = False
        # Need to create new set() as its changed during iteration
        data_depencencies = {k: set([v for v in values]) for k, values in node.context[context_key].items()}

        if node.fathers:
            for father in node.fathers:
                for key, items in father.context[context_key].items():
                    if key not in node.context[context_key]:
                        changed = True
                        updated_dependencies = True
                        node.context[context_key][key] = set(items)
                    for item in items:
                        if not item in node.context[context_key][key]:
                            node.context[context_key][key].add(item)
                            changed = True
                            updated_dependencies = True

        for key, items in data_depencencies.items():
            for item in items:
                if item in data_depencencies:
                    additional_items = node.context[context_key][item]
                    for additional_item in additional_items:
                        if not additional_item in items and additional_item != key:
                            changed = True
                            updated_dependencies = True
                            node.context[context_key][key].add(additional_item)
    node.context[context_key_non_ssa] = convert_to_non_ssa(node.context[context_key])

    return updated_dependencies

def propagate_contract(contract, context_key, context_key_non_ssa):
    transitive_close_dependencies(contract, context_key, context_key_non_ssa)


def add_dependency_member(function, ir, is_protected):
    ssa = function.context[KEY_SSA]
    ssa_unprotected = function.context[KEY_SSA_UNPROTECTED]

    if isinstance(ir, PhiMemberMust):
        for key, item in ir.phi_info.items():
            key = (ir.lvalue, key)
            ssa[key] = set([item])
            if not is_protected:
                ssa_unprotected[key] = set([item])
    if isinstance(ir, PhiMemberMay):
        for key, item in ir.phi_info.items():
            key = (ir.lvalue, key)
            ssa[key].add(item)
            if not is_protected:
                ssa_unprotected[key].add(item)
    if isinstance(ir, AccessMember):
        key = ir.lvalue
        ssa[key] = {(ir.variable_left, ir.variable_right)}
        if not is_protected:
            ssa_unprotected[key] = {(ir.variable_left, ir.variable_right)}

def add_dependency(function, ir, is_protected):

    ssa = function.context[KEY_SSA]
    ssa_unprotected = function.context[KEY_SSA_UNPROTECTED]
    if isinstance(ir.lvalue, MemberVariable):
        key = (ir.lvalue.base, ir.lvalue.member)
    else:
        key = ir.lvalue

    if not key in ssa:
        ssa[key] = set()
        if not is_protected:
            ssa_unprotected[key] = set()
    if isinstance(ir, Index):
        read = [ir.variable_left]
    elif isinstance(ir, InternalCall):
        read = ir.function.return_values_ssa
    else:
        read = ir.read

    # Update for Structure variables
    # Iterate over each member field
    if isinstance(ir.lvalue.type, UserDefinedType) and isinstance(ir.lvalue.type.type, Structure):
        members = ir.lvalue.type.type.elems.values()
        for member in members:
            key = (ir.lvalue, Constant(member.name))
            if not key in ssa:
                ssa[key] = set()
            [ssa[key].add((v, Constant(member.name))) for v in read]

            if not is_protected:
                if not key in ssa_unprotected:
                    ssa_unprotected[key] = set()
                [ssa_unprotected[key].add((v, Constant(member.name))) for v in read]
    # Normal taint
    else:
        [ssa[key].add(v) for v in read if not isinstance(v, (Constant, MemberVariable))]
        [ssa[key].add((v.base, v.member)) for v in read if isinstance(v, MemberVariable)]

        if not is_protected:
            [ssa_unprotected[key].add(v) for v in read if not isinstance(v, (Constant, MemberVariable))]
            [ssa_unprotected[key].add((v.base, v.member)) for v in read if isinstance(v, MemberVariable)]


# def compute_dependency_function_old(function):
#     if KEY_SSA in function.context:
#         return
#
#     function.context[KEY_SSA] = defaultdict(set)
#     function.context[KEY_SSA_UNPROTECTED] = defaultdict(set)
#
#     is_protected = function.is_protected()
#     for node in function.nodes:
#         for ir in node.irs_ssa:
#             if isinstance(ir, OperationWithLValue) and ir.lvalue:
#                 # if isinstance(ir.lvalue, LocalIRVariable) and ir.lvalue.is_storage:
#                 #     continue
#                 # if isinstance(ir.lvalue, (IndexVariable, MemberVariable)):
#                 #     lvalue = ir.lvalue.points_to
#                 #     if lvalue:
#                 #         add_dependency(lvalue, function, ir, is_protected)
#                 if isinstance(ir, (PhiMemberMust, PhiMemberMay, AccessMember)):
#                     add_dependency_member(function, ir, is_protected)
#                 else:
#                     add_dependency(function, ir, is_protected)
#
#     nodes_end = [node for node in function.nodes if node.will_return]
#
#     function.context[KEY_NON_SSA] = convert_to_non_ssa(function.context[KEY_SSA])
#     function.context[KEY_NON_SSA_UNPROTECTED] = convert_to_non_ssa(function.context[KEY_SSA_UNPROTECTED])

def compute_dependency_node(node, is_protected):
    if KEY_SSA in node.context:
        return

    node.context[KEY_SSA] = defaultdict(set)
    node.context[KEY_SSA_UNPROTECTED] = defaultdict(set)

    for ir in node.irs_ssa:
        if isinstance(ir, OperationWithLValue) and ir.lvalue:
            if isinstance(ir, (PhiMemberMust, PhiMemberMay, AccessMember)):
                add_dependency_member(node, ir, is_protected)
            else:
                add_dependency(node, ir, is_protected)


    node.context[KEY_NON_SSA] = convert_to_non_ssa(node.context[KEY_SSA])
    node.context[KEY_NON_SSA_UNPROTECTED] = convert_to_non_ssa(node.context[KEY_SSA_UNPROTECTED])

    for dom in node.dominance_exploration_ordered:
        compute_dependency_node(dom, is_protected)


def compute_dependency_function(function):
    if KEY_SSA in function.context:
        return

    function.context[KEY_SSA] = defaultdict(set)
    function.context[KEY_SSA_UNPROTECTED] = defaultdict(set)

    is_protected = function.is_protected()

    compute_dependency_node(function.entry_point, is_protected)

    nodes = function.nodes_ordered_dominators

    while nodes:
        node = nodes[0]
        nodes = nodes[1:]

        if transitive_close_node_dependencies(node, KEY_SSA, KEY_NON_SSA):
            nodes.append(node)
        if transitive_close_node_dependencies(node, KEY_SSA_UNPROTECTED, KEY_NON_SSA_UNPROTECTED):
            if not node in nodes:
                nodes.append(node)

    nodes_end = [node for node in function.nodes if node.will_return]

    nodes = [x for x in nodes_end]

    if nodes:
        initial_node = nodes[0]
        nodes = nodes[1:]
        initial_context = initial_node.context
        ssa = defaultdict(set, initial_context[KEY_SSA])
        ssa_unprotected = defaultdict(set, initial_context[KEY_SSA_UNPROTECTED])

        non_ssa = convert_to_non_ssa(ssa)
        non_ssa_unprotected = convert_to_non_ssa(ssa_unprotected)

        for other_node in nodes:
            other_context = other_node.context
            for key, items in other_context[KEY_SSA].items():
                ssa[key] = ssa[key].union(items)
            for key, items in other_context[KEY_SSA_UNPROTECTED].items():
                ssa_unprotected[key] = ssa_unprotected[key].union(items)

            for key, items in convert_to_non_ssa(other_context[KEY_SSA]).items():
                non_ssa[key] = non_ssa[key].union(items)
            for key, items in convert_to_non_ssa(other_context[KEY_SSA_UNPROTECTED]):
                non_ssa_unprotected[key] = non_ssa_unprotected[key].union(items)

    else:
        ssa = defaultdict(set)
        ssa_unprotected = defaultdict(set)
        non_ssa = defaultdict(set)
        non_ssa_unprotected = defaultdict(set)

    # ssa_last = {k: v for (k, v) in ssa.items() if k in ssa_last_names.values()}
    # ssa_unprotected_last = {k: v for (k, v) in ssa_unprotected.items() if k in ssa_last_names_unprotected.values()}

    # print(len(ssa))
    # print(len(ssa_last))
    function.context[KEY_SSA] = ssa
    function.context[KEY_SSA_UNPROTECTED] = ssa_unprotected
    function.context[KEY_NON_SSA] = non_ssa
    function.context[KEY_NON_SSA_UNPROTECTED] = non_ssa_unprotected

    # pprint_dependency(function)

def convert_variable_to_non_ssa(v):
    if isinstance(v, (LocalIRVariable, StateIRVariable, TemporaryVariableSSA,
                      IndexVariableSSA, TupleVariableSSA, MemberVariableSSA)):
        return v.non_ssa_version
    if isinstance(v, tuple) and len(v) == 2:
        base = v[0]
        member = v[1]
        return (base.non_ssa_version, member)
    assert isinstance(v, (Constant, SolidityVariable, Contract, Enum, SolidityFunction, Structure, Function, Type))
    return v

def _get_index(v):
    if isinstance(v, tuple):
        return v[0].index
    return v.index

def convert_to_non_ssa(data_depencies):
    # Keep only the last name
    # Assume that last name == last index
    last_name = dict()
    for v in data_depencies.keys():
        if isinstance(v, tuple):
            k = (v[0].non_ssa_version, v[1])
        else:
            k = v.non_ssa_version
        if not k in last_name:
            last_name[k] = v
        elif _get_index(last_name[k]) < _get_index(v):
            last_name[k] = v

    data_last = {k: v for (k, v) in data_depencies.items() if k in last_name.values()}

    # Need to create new set() as its changed during iteration
    ret = dict()
    for (k, values) in data_last.items():
        var = convert_variable_to_non_ssa(k)
        if not var in ret:
            ret[var] = set()
        ret[var] = ret[var].union(set([convert_variable_to_non_ssa(v) for v in
                                       values]))

    return ret
