"""
    Compute the data depenency between all the SSA variables
"""
from collections import defaultdict
from prettytable import PrettyTable

from slither.core.cfg.node import Node
from slither.core.declarations import (Contract, Enum, Function,
                                       SolidityFunction, SolidityVariable,
                                       SolidityVariableComposed, Structure)
from slither.core.solidity_types import UserDefinedType, ArrayType, MappingType
from slither.slithir.operations import Index, OperationWithLValue, InternalCall, PhiMemberMust, PhiMemberMay, \
    AccessMember, Phi, Balance
from slither.slithir.variables import (Constant, LocalIRVariable,
                                       IndexVariable, IndexVariableSSA,
                                       StateIRVariable, MemberVariable, MemberVariableSSA,
                                       TemporaryVariableSSA, TupleVariableSSA, TemporaryVariable)
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


def get_dependencies(variable, context, only_unprotected=False, is_ssa=False):
    '''
    Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
        is_ssa (bool)
    Returns:
        list(Variable)
    '''
    if isinstance(variable, tuple) and len(variable)>2:
        return _get_dependencies_from_nested(variable, context, only_unprotected, is_ssa)
    assert isinstance(context, (Contract, Function, Node))
    assert isinstance(only_unprotected, bool)
    print([str(x) if not isinstance(x, tuple) else str((str(x[0]), str(x[1]))) for x in context.context[KEY_NON_SSA].keys()])
    if only_unprotected:
        return context.context[KEY_SSA_UNPROTECTED if is_ssa else KEY_NON_SSA_UNPROTECTED].get(variable, [])
    return context.context[KEY_SSA if is_ssa else KEY_NON_SSA].get(variable, [])


def _get_dependencies_from_nested(variables, context, only_unprotected=False, is_ssa=False):
    if only_unprotected:
        context = context.context[KEY_SSA_UNPROTECTED if is_ssa else KEY_NON_SSA_UNPROTECTED]
    else:
        context = context.context[KEY_SSA if is_ssa else KEY_NON_SSA]

    # print(f'Try {[str(x) for x in variables]}')
    next_level = [variables[0]]
    variables = variables[1:]
    # print(f'Try {[str(x) for x in variables]}')
    while variables:
        next_next = []
        variable = variables[0]
        variables = variables[1:]
        for next in next_level:
            key = (next, variable)
            #       print(f'First key {next}.{variable}')
            # print(key)
            if key in context:
                next_next += context[key]
            # else:
            #     print(f'Missing {next}.{variable}')
        next_level = next_next

    return next_level


def get_dependencies_ssa(variable, context, only_unprotected=False):
    '''
    Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        list(Variable)
    '''
    if isinstance(variable, tuple):
        return _get_dependencies_from_nested_ssa(variable, context, only_unprotected)
    assert isinstance(context, (Contract, Function, Node))
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_SSA].get(variable, [])
    return context.context[KEY_SSA_UNPROTECTED].get(variable, [])


def _get_dependencies_from_nested_ssa(variables, context, only_unprotected=False):
    if only_unprotected:
        context = context.context[KEY_SSA]
    else:
        context = context.context[KEY_SSA_UNPROTECTED]

    # print(f'Try {[str(x) for x in variables]}')
    next_level = [variables[0]]
    variables = variables[1:]
    # print(f'Try {[str(x) for x in variables]}')
    while variables:
        next_next = []
        variable = variables[0]
        variables = variables[1:]
        for next in next_level:
            key = (next, variable)
            #       print(f'First key {next}.{variable}')
            # print(key)
            if key in context:
                next_next += context[key]
            # else:
            #     print(f'Missing {next}.{variable}')
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

TOP = '*'


# endregion
###################################################################################
###################################################################################
# region Temporary class
###################################################################################
###################################################################################

class IndirectTaint:
    """
    Class use to capture the taint generated by phi operation

    For Phi operations we add as dependencies
    The dependencies of the right elements
    Ex:
    if():
       m_1 = a_1
    else
       m_2 = b_1
    m_3 = Phi(m_1, m_2)
    The deps of m_3 are (a_1, b_1) and not (m1, m2)
    Otherwise it creates an implicite dependecy from m to m

    As the trasitive closure is computed later, we use this class
    to keep the information that the taint is not direct

    """

    def __init__(self, item):
        self._item = item

    @property
    def item(self):
        return self._item

    def __str__(self):
        return f'IndirectTaint({self.item})'


def _remove_indirect_taint(node, context):
    for k, items in node.context[context].items():
        node.context[context][k] = set([i for i in items if not isinstance(i, IndirectTaint)])


# endregion
###################################################################################
###################################################################################
# region PrettyPrint
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


def _convert(d):
    if isinstance(d, tuple):
        return '.'.join([x.name for x in d])
    return d.name


def _get(v, c):
    return list(set([_convert(d) for d in get_dependencies(v, c) if not isinstance(d, (TemporaryVariable,
                                                                                       IndexVariable, MemberVariable,
                                                                                       tuple))]))


def _get_offsets(v, context):
    # assert isinstance(v.type, (ArrayType, MappingType))

    ret = []
    for k, values in context.items():
        # if isinstance(k, tuple):
        #     print(f'K[0]: {k[0]} == {v} ({k[0] == v}')
        if isinstance(k, tuple) and k[0] == v:
            ret.append((k[1], values))

    return ret


def _add_row_rec(v, c, key, table, is_ssa):
    # print(f'v: {v} ({type(v.type)})')
    # print(f'key: {key}')

    if isinstance(v.type, UserDefinedType) and isinstance(v.type.type, Structure):
        for elem in v.type.type.elems.values():
            deps = []
            print(f'Test {(str(v), str(elem))}')
            print(get_dependencies((v, elem), c, is_ssa))
            print(is_ssa)
            for dep in get_dependencies((v, elem), c, is_ssa):
                print(f"### dep: {dep}")
                if (isinstance(elem.type, UserDefinedType) and isinstance(elem.type.type, Structure) or
                        isinstance(elem.type, (ArrayType, MappingType))):
                    _add_row_rec(dep, c, f'{key}.{elem}', table, is_ssa)
                else:
                    deps.append(str(dep))
            if deps:
                table.add_row([f'{key}.{elem}', str(deps)])
    elif isinstance(v.type, (ArrayType, MappingType)):
        #   print()
        for (offset, values) in _get_offsets(v, c.context[KEY_SSA if is_ssa else KEY_NON_SSA]):
            # print(offset)
            # print(values)
            vals = []
            for value in values:
                #          print(f'values: {value}')
                if isinstance(value, tuple):
                    # if value[1] == TOP:
                    #print(value[0])
                    continue
                # print(f'value type: {type(value.type)}')
                if (isinstance(value.type, UserDefinedType) and isinstance(value.type.type, Structure) or
                        isinstance(value.type, (ArrayType, MappingType))):
                    if offset == TOP:
                        _add_row_rec(value, c, f'{key}', table, is_ssa)
                    else:
                        _add_row_rec(value, c, f'{key}[{offset}]', table, is_ssa)
                else:
                    vals.append(str(value))
            if vals:
                table.add_row([f'{key}[{offset}]', str(vals)])
    else:
        table.add_row([v.name, _get(v, c)])


def _add_row(v, c, table, is_ssa):
    _add_row_rec(v, c, v, table, is_ssa=is_ssa)


# def _add_row(v, c, table):
#     context = c.context[KEY_NON_SSA]
#
#     print(f'value: {v}')
#     for k, values in context.items():
#         if isinstance(k, tuple) and k[0] == v:
#             table.add_row([str([[str(kk) for kk in k]]), [str(v) for v in values]])


def _convert_string(v):
    if isinstance(v, (list, tuple)):
        return str([_convert_string(vv) for vv in v])
    return str(v)


def _add_rows(c, table):
    context = c.context[KEY_SSA]

    for k, values in context.items():
        values = str([_convert_string(v) for v in values])
        if isinstance(k, tuple):
            table.add_row([str([[str(kk) for kk in k]]), values])
        else:
            table.add_row([str(k), values])

    table.add_row(['####', '####'])

    context = c.context[KEY_NON_SSA]

    for k, values in context.items():
        values = str([_convert_string(v) for v in values])
        if isinstance(k, tuple):
            table.add_row([str([[str(kk) for kk in k]]), values])
        else:
            table.add_row([str(k), values])

def _add_row_old(v, c, table):
    if isinstance(v.type, UserDefinedType) and isinstance(v.type.type, Structure):
        for elem in v.type.type.elems.values():
            if isinstance(elem.type, UserDefinedType) and isinstance(elem.type.type, Structure):
                for elem_nested in elem.type.type.elems.values():
                    table.add_row([f'{v.name}.{elem}.{elem_nested.name}',
                                   _get([v, Constant(elem.name), Constant(elem_nested.name)], c)])
            else:
                table.add_row([f'{v.name}.{elem}', _get((v, Constant(elem.name)), c)])
    elif isinstance(v.type, (ArrayType, MappingType)):
        for offset in _get_offsets(v, c.context[KEY_SSA]):
            if isinstance(offset.type, (ArrayType, MappingType)):
                for offset_nested in _get_offsets(offset, c.context[KEY_SSA]):
                    table.add_row([f'{v.name}[{offset}][{offset_nested}]',
                                   _get([v, offset, offset_nested], c)])
            else:
                table.add_row([f'{v.name}[{offset}]', _get((v, offset), c)])
    else:
        table.add_row([v.name, _get(v, c)])


def pprint_dependency_table(context):
    table = PrettyTable(['Variable', 'Dependencies'])

    if isinstance(context, Contract):
        for v in context.state_variables:
            _add_row(v, context, table, False)

    if isinstance(context, Function):
        #_add_rows(context, table)
        #table.add_row(['####', '####'])
        for v in context.contract.state_variables:
            _add_row(v, context, table, False)
        for v in context.local_variables:
            _add_row(v, context, table, False)

    if isinstance(context, Node):
        _add_rows(context, table)
        table.add_row(['####', '####'])
        state_variables_ssa = set()
        # for node in context.function.nodes:
        #    state_variables_ssa |= set(node.ssa_state_variables_written)
        # for v in state_variables_ssa:
        for v in context.ssa_state_variables_written:
            _add_row(v, context, table, True)

    return table


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

        #print(f'\n\n\n\n\n\nFunction done')
        #pprint_dependency(function)

        propagate_function(contract,
                           function,
                           KEY_SSA,
                           KEY_NON_SSA)

        propagate_function(contract,
                           function,
                           KEY_SSA_UNPROTECTED,
                           KEY_NON_SSA_UNPROTECTED)

        #pprint_dependency(function)

        if function.visibility in ['public', 'external']:
            [slither.context[KEY_INPUT].add(p) for p in function.parameters]
            [slither.context[KEY_INPUT_SSA].add(p) for p in function.parameters_ssa]
        # print('############ after propage')
        # pprint_dependency(function)
        # print('################################################')

    propagate_contract(contract, KEY_SSA, KEY_NON_SSA)
    propagate_contract(contract, KEY_SSA_UNPROTECTED, KEY_NON_SSA_UNPROTECTED)


def propagate_function(contract, function, context_key, context_key_non_ssa):
    # transitive_close_dependencies(function, context_key, context_key_non_ssa)
    # Propage data dependency
    data_depencencies = function.context[context_key]

    for (key, values) in data_depencencies.items():
        #print(f'key: {key}')
        contract.context[context_key][key] |= set(values)


#    contract.context[context_key_non_ssa] |= convert_to_non_ssa(data_depencencies)

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


def _propagate_indirect_taint_on_member(node, context, father, key, item):
    """
     Propagate indirect taint on structure member
    For example v  = phi(indirect(a), indirect(b))
    where v, a and b are structure, each member must be updated
    """
    updated_dependencies = False
    members = item.type.type.elems.values()
    for member in members:
        key_father = (item, Constant(member.name))
        key_node = (key, Constant(member.name))
        if not father.context[context][key_father].issubset(node.context[context][key_node]):
            node.context[context][key_node] |= father.context[context][key_father]
            updated_dependencies = True
    return updated_dependencies


def _propagate_indirect_taint(node, context_key):
    # Convert IndirectTaint
    updated_dependencies = False

    # Need to create new set() as its changed during iteration
    data_depencencies = {k: set([v for v in values]) for k, values in node.context[context_key].items()}

    for key, items in data_depencencies.items():
        new_items = set()
        for item in items:
            if isinstance(item, IndirectTaint):
                new_items.add(item.item)
        if new_items:
            for item in new_items:
                for father in node.fathers:
                    if isinstance(item.type, UserDefinedType) and isinstance(item.type.type, Structure):
                        updated_dependencies |= _propagate_indirect_taint_on_member(node, context_key, father, key,
                                                                                    item)
                    elif not father.context[context_key][item].issubset(node.context[context_key][key]):
                        node.context[context_key][key] |= father.context[context_key][item]
                        updated_dependencies = True
    return updated_dependencies


def _propagate_phi_taint(node, context_key):
    updated_dependencies = False

    taint = node.context[context_key]

    for ir in node.irs_ssa:
        if isinstance(ir, PhiMemberMust):
            for (offset, values) in _get_offsets(ir.base, taint):
                if offset in ir.phi_info:
                    # print(f' offset {offset}')
                    continue
                key = (ir.lvalue, offset)
                if not set(values).issubset(taint[key]):
                    taint[key] |= values
                    updated_dependencies = True

            # If the key of the Phi is not a Constant, must update all
            # the other elements
            # Example
            #         mapp[0][0] = a;
            #         mapp[0][b] = b;
            # mapp[0][0] might be 'b'
            for key, item in ir.phi_info.items():
                if isinstance(key, Constant):
                    continue
                for (offset, values) in _get_offsets(ir.lvalue, taint):
                    key = (ir.lvalue, offset)
                    if item not in taint[key]:
                        taint[key] |= {item}
                        updated_dependencies = True

        if isinstance(ir, Index):
            # Update index information
            # If the index is from a nested object
            # Need to update all the index of the new element
            # to point to the previous ones
            # Example:
            #         mapp[0][0] = a;
            #         mapp[0][1] = b;
            # mapp[0][1] will create index_x_0 -> mappX[0]
            # All the offsets of index_x_0 must points to the mappX[0] offsets
            for t in node.context[context_key][ir.lvalue]:
                if isinstance(t, IndexVariableSSA):
                    key = (ir.variable_left, ir.variable_right)
                    for k in taint[key]:
                        for (offset, values) in _get_offsets(k, taint):
                            key = (ir.lvalue, offset)
                            if not set(values).issubset(taint[key]):
                                taint[key] |= values
                                updated_dependencies = True
            # for (offset, values) in _get_offsets(ir.base, taint):

    return updated_dependencies


def transitive_close_node_dependencies(node, context_key):
    # transitive closure
    changed = True
    updated_dependencies = False

    if context_key not in node.context:
        node.context[context_key] = defaultdict(set)

    #updated_dependencies |= _propagate_indirect_taint(node, context_key)

    #updated_dependencies |= _propagate_phi_taint(node, context_key)

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

    return updated_dependencies


def propagate_contract(contract, context_key, context_key_non_ssa):
    transitive_close_dependencies(contract, context_key, context_key_non_ssa)


def add_dependency_member(function, ir, is_protected):
    ssa = function.context[KEY_SSA]
    ssa_unprotected = function.context[KEY_SSA_UNPROTECTED]

    if isinstance(ir, PhiMemberMust):
        for key, item in ir.phi_info.items():
            key = (ir.lvalue, key)
            if isinstance(key, Constant):
                ssa[key] = {item}
            else:
                ssa[key] |= {item}

                # _key = (ir.lvalue, TOP)
                # ssa[_key] |= {item}
            if not is_protected:
                if isinstance(key, Constant):
                    ssa_unprotected[key] = {item}
                else:
                    ssa_unprotected[key] |= {item}

        # key = (ir.lvalue, TOP)
        # ssa[key] |= {ir.base}
        # if not is_protected:
        #     ssa_unprotected[key] |= {ir.base}

    elif isinstance(ir, PhiMemberMay):
        for key, item in ir.phi_info.items():
            key = (ir.lvalue, key)
            ssa[key] |= {item}
            if not is_protected:
                ssa_unprotected[key] |= {item}

        # key = (ir.lvalue, TOP)
        # ssa[key] = {ir.base}
        # if not is_protected:
        #     ssa_unprotected[key] = {ir.base}

    elif isinstance(ir, AccessMember):
        key = ir.lvalue
        ssa[key] = {(ir.variable_left, ir.variable_right)}
        if not is_protected:
            ssa_unprotected[key] = {(ir.variable_left, ir.variable_right)}

    elif isinstance(ir, Index):
        # key = (ir.lvalue, ir.variable_right)
        key = ir.lvalue
        ssa[key] = {(ir.variable_left, ir.variable_right)}
        if not is_protected:
            ssa_unprotected[key] = {(ir.variable_left, ir.variable_right)}


def add_dependency(function, ir, is_protected):
    ssa = function.context[KEY_SSA]
    ssa_unprotected = function.context[KEY_SSA_UNPROTECTED]

    # TODO: fix Balance support
    if isinstance(ir, Balance):
        key = ir.lvalue
    elif isinstance(ir.lvalue, MemberVariable):
        key = (ir.lvalue.base, ir.lvalue.member)
    elif isinstance(ir.lvalue, IndexVariable):
        key = (ir.lvalue.base, ir.lvalue.offset)
    else:
        key = ir.lvalue

    if isinstance(ir, Index):
        read = [ir.variable_left]
    elif isinstance(ir, InternalCall):
        read = ir.function.return_values_ssa
    else:
        read = ir.read

    # For Phi operations we add as dependencies
    # The dependencies of the right elements
    # Ex:
    # if():
    #    m_1 = a_1
    # else
    #    m_2 = b_1
    # m_3 = Phi(m_1, m_2)
    # The deps of m_3 are (a_1, b_1) and not (m1, m2)
    # Otherwise it creates an implicite dependecy from m to m
    print(ir)
    if isinstance(ir, Phi):
        if isinstance(ir.lvalue.type, UserDefinedType) and isinstance(ir.lvalue.type.type, Structure):
            members = ir.lvalue.type.type.elems.values()
            for member in members:
                key = (ir.lvalue, Constant(member.name))
                [ssa[key].add((v, Constant(member.name))) for v in read]
                if not is_protected:
                    [ssa_unprotected[key].add((v, Constant(member.name))) for v in read]
        else:
            # TODO: might remove this
            for v in read:
                if isinstance(v, (IndexVariable, MemberVariable)):
                    ssa[key] |= {IndirectTaint(v)}
                    if not is_protected:
                        ssa_unprotected[key] |= {IndirectTaint(v)}
                else:
                    ssa[key] |= {v}

    # # Update for Structure variables
    # # Iterate over each member field
    # elif isinstance(ir.lvalue.type, UserDefinedType) and isinstance(ir.lvalue.type.type, Structure):
    #     members = ir.lvalue.type.type.elems.values()
    #     for member in members:
    #         key = (ir.lvalue, Constant(member.name))
    #         [ssa[key].add((v, Constant(member.name))) for v in read]
    #         if not is_protected:
    #             [ssa_unprotected[key].add((v, Constant(member.name))) for v in read]
    # Normal taint
    else:
        [ssa[key].add(v) for v in read if (not isinstance(v, (Constant, MemberVariable, IndexVariable)))]
        [ssa[key].add((v.base, v.member)) for v in read if (isinstance(v, MemberVariable))]
        [ssa[key].add((v.base, v.offset)) for v in read if isinstance(v, IndexVariable)]

        if not is_protected:
            [ssa_unprotected[key].add(v) for v in read if not isinstance(v, (Constant, MemberVariable, IndexVariable))]
            [ssa_unprotected[key].add((v.base, v.member)) for v in read if isinstance(v, MemberVariable)]
            [ssa_unprotected[key].add((v.base, v.offset)) for v in read if isinstance(v, IndexVariable)]


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
    if not node:
        return
    if KEY_SSA in node.context:
        return

    node.context[KEY_SSA] = defaultdict(set)
    node.context[KEY_SSA_UNPROTECTED] = defaultdict(set)

    for ir in node.irs_ssa:
        if isinstance(ir, OperationWithLValue) and ir.lvalue:
            if isinstance(ir, (PhiMemberMust, PhiMemberMay, AccessMember, Index)):
                add_dependency_member(node, ir, is_protected)
            else:
                add_dependency(node, ir, is_protected)

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
        if transitive_close_node_dependencies(node, KEY_SSA):
            nodes.append(node)
        else:
            _remove_indirect_taint(node, KEY_SSA)
            node.context[KEY_NON_SSA] = convert_to_non_ssa(node.context[KEY_SSA])
        if transitive_close_node_dependencies(node, KEY_SSA_UNPROTECTED):
            if node not in nodes:
                nodes.append(node)
        else:
            _remove_indirect_taint(node, KEY_SSA_UNPROTECTED)
            node.context[KEY_NON_SSA_UNPROTECTED] = convert_to_non_ssa(node.context[KEY_SSA_UNPROTECTED])

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
            for key, items in convert_to_non_ssa(other_context[KEY_SSA_UNPROTECTED]).items():
                non_ssa_unprotected[key] = non_ssa_unprotected[key].union(items)

    else:
        ssa = defaultdict(set)
        ssa_unprotected = defaultdict(set)
        non_ssa = defaultdict(set)
        non_ssa_unprotected = defaultdict(set)

    function.context[KEY_SSA] = ssa
    function.context[KEY_SSA_UNPROTECTED] = ssa_unprotected
    function.context[KEY_NON_SSA] = non_ssa
    function.context[KEY_NON_SSA_UNPROTECTED] = non_ssa_unprotected


def convert_variable_to_non_ssa(v):
    if isinstance(v, (LocalIRVariable, StateIRVariable, TemporaryVariableSSA,
                      IndexVariableSSA, TupleVariableSSA, MemberVariableSSA)):
        return v.non_ssa_version
    if isinstance(v, tuple) and len(v) == 2:
        base = v[0]
        member = v[1]
        if isinstance(base, SolidityVariable):
            return (base, member)
        else:
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
            if isinstance(v[0], SolidityVariable):
                k = (v[0], v[1])
            else:
                k = (v[0].non_ssa_version, v[1])
        elif isinstance(v, Constant):
            k = v
        else:
            k = v.non_ssa_version
        if k not in last_name:
            last_name[k] = v
        elif _get_index(last_name[k]) < _get_index(v):
            last_name[k] = v

    data_last = {k: v for (k, v) in data_depencies.items() if k in last_name.values()}

    # Need to create new set() as its changed during iteration
    ret = defaultdict(set)
    for (k, values) in data_last.items():
        var = convert_variable_to_non_ssa(k)
        ret[var] |= set([convert_variable_to_non_ssa(v) for v in values])

    return ret
