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

def _to_tuple(l, n):
    return tuple(list(l) + [n])


def _convert_elem(elem, accesses):
    if isinstance(elem, (tuple, list)) and len(elem) > 3:
        next_level = [elem[0:2]]
        sts = elem[2:]
        for st in sts:
            level = set([n for n in next_level])
            next_level = set()
            for l in level:
                k = _to_tuple(l, st)
                next_level |= accesses[k]
        return [tuple(list(n)) for n in next_level]
    return [elem]


# _convert_elem(('n2','m','st','val1'), Test())

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
    assert isinstance(context, (Contract, Function, Node))
    if isinstance(variable, Constant):
        return False
    if variable == source:
        return True
    context = context.context
    if only_unprotected:
        variable = _convert_elem(variable, context[KEY_NON_SSA_UNPROTECTED])
        return source in context[KEY_NON_SSA_UNPROTECTED].get(variable)
    sources = _convert_elem(source, context[KEY_ACCESS_NON_SSA])
    for source in sources:
        variables = _convert_elem(variable, context[KEY_ACCESS_NON_SSA])
        for var in variables:
            if source in context[KEY_NON_SSA].get(var):
                return True
    return False


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
    assert isinstance(context, (Contract, Function, Node))
    context = context.context
    if isinstance(variable, Constant):
        return False
    if variable == source:
        return True
    if only_unprotected:
        return source in context[KEY_SSA_UNPROTECTED].get(variable)
    sources = _convert_elem(source, context[KEY_ACCESS_SSA])
    for source in sources:
        variables = _convert_elem(variable, context[KEY_ACCESS_SSA])
        for var in variables:
            if source in context[KEY_ACCESS_SSA].get(var):
                return True
    return False


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
    assert isinstance(context, (Contract, Function, Node))
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
        ignore_generic_taint:
    Returns:
        bool
    '''
    assert isinstance(context, (Contract, Function, Node))
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
    assert isinstance(context, (Contract, Function, Node))
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_SSA_UNPROTECTED if is_ssa else KEY_NON_SSA_UNPROTECTED].get(variable)
    return context.context[KEY_SSA if is_ssa else KEY_NON_SSA].get(variable)


def get_dependencies_ssa(variable, context, only_unprotected=False):
    '''
    Args:
        variable
        context (Contract|Function)
        only_unprotected (bool): True only unprotected function are considered
    Returns:
        list(Variable)
    '''
    assert isinstance(context, (Contract, Function, Node))
    assert isinstance(only_unprotected, bool)
    if only_unprotected:
        return context.context[KEY_SSA].get(variable)
    return context.context[KEY_SSA_UNPROTECTED].get(variable)


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

KEY_ACCESS_SSA = "DATA_DEPENDENCY_INPUT_ACCESS_SSA"
KEY_ACCESS_NON_SSA = "DATA_DEPENDENCY_INPUT_ACCESS_NON_SSA"

TOP = '*'


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

def _add_row_rec(v, c, key, table, is_ssa):

    if isinstance(v.type, UserDefinedType) and isinstance(v.type.type, Structure):
        for elem in v.type.type.elems.values():
            deps = []
            for dep in get_dependencies((v, elem.name), c, is_ssa=is_ssa):
                if (isinstance(elem.type, UserDefinedType) and isinstance(elem.type.type, Structure) or
                        isinstance(elem.type, (ArrayType, MappingType))):
                    _add_row_rec(dep, c, f'{key}.{elem}', table, is_ssa)
                else:
                    if isinstance(dep, tuple):
                        deps.append(str((str(dep[0]), str(dep[1]))))
                    else:
                        deps.append(str(dep))

            if deps:
                table.add_row([f'{key}.{elem}',
                               str(deps),
                               is_tainted((key, elem), c)])
    else:
        table.add_row([v.name, _get(v, c), is_tainted(v, c)])


def _add_row(v, c, table, is_ssa):
    _add_row_rec(v, c, v, table, is_ssa=is_ssa)


def _convert_string(v):
    if isinstance(v, (list, tuple)):
        return str([_convert_string(vv) for vv in v])
    return str(v)


def _add_rows(c, table):
    context = c.context[KEY_SSA]

    for k, values in context.items():
        values = str([_convert_string(v) for v in values])
        if isinstance(k, tuple):
            table.add_row([str([[str(kk) for kk in k]]), values, is_tainted(k, c)])
        else:
            table.add_row([str(k), values, is_tainted(k, c)])

    table.add_row(['####', '####', '####'])

    context = c.context[KEY_NON_SSA]

    for k, values in context.items():
        values = str([_convert_string(v) for v in values])
        if isinstance(k, tuple):
            table.add_row([str([[str(kk) for kk in k]]), values, is_tainted(k, c)])
        else:
            table.add_row([str(k), values, is_tainted(k, c)])


def pprint_dependency_table(context):
    table = PrettyTable(['Variable', 'Dependencies', 'Is tainted'])

    if isinstance(context, Contract):
        for v in context.state_variables:
            _add_row(v, context, table, False)

        table.add_row(['####', '####', '####'])
        for key, elems in context.context[KEY_NON_SSA].items():
            table.add_row(
                [[_convert_string(x) for x in key] if isinstance(key, (tuple, list, set)) else _convert_string(key),
                 [_convert_string(x) for x in elems] if isinstance(elems, (tuple, list, set)) else _convert_string(
                     elems), '####'])

        table.add_row(['####', '####', '####'])
        for key, elems in context.context[KEY_SSA].items():
            table.add_row(
                [[_convert_string(x) for x in key] if isinstance(key, (tuple, list, set)) else _convert_string(key),
                 [_convert_string(x) for x in elems] if isinstance(elems, (tuple, list, set)) else _convert_string(
                     elems), '####'])

    if isinstance(context, Function):
        for v in context.contract.state_variables:
            _add_row(v, context, table, False)
        for v in context.local_variables:
            _add_row(v, context, table, False)

        table.add_row(['####', '####', '####'])
        for key, elems in context.context[KEY_SSA].items():
            table.add_row(
                [[_convert_string(x) for x in key] if isinstance(key, (tuple, list, set)) else _convert_string(key),
                 [_convert_string(x) for x in elems] if isinstance(elems, (tuple, list, set)) else _convert_string(
                     elems), '####'])

        table.add_row(['####', '####', '####'])
        for key, elems in context.context[KEY_NON_SSA].items():
            table.add_row(
                [[_convert_string(x) for x in key] if isinstance(key, (tuple, list, set)) else _convert_string(key),
                 [_convert_string(x) for x in elems] if isinstance(elems, (tuple, list, set)) else _convert_string(
                     elems), '####'])

    if isinstance(context, Node):
        _add_rows(context, table)
        table.add_row(['####', '####', '####'])
        state_variables_ssa = set()
        # for node in context.function.nodes:
        #    state_variables_ssa |= set(node.ssa_state_variables_written)
        # for v in state_variables_ssa:
        for v in context.ssa_state_variables_written:
            print(v)
            _add_row(v, context, table, True)

    return table


# endregion
###################################################################################
###################################################################################
# region Analyses
###################################################################################
###################################################################################


class Taint:

    def __init__(self, taints=None):
        if taints is None:
            self._taints = defaultdict(set)
        else:
            self._taints = taints

    @property
    def taints(self):
        """

        :return:
        """
        return self._taints

    def get(self, key):
        """

        :param key:
        :return:
        """
        return self._taints.get(key, set())
        # return self._get(key, set())

    def _get(self, key, seen):
        print(seen)
        if isinstance(key, Constant):
            return set()
        if key in seen:
            return set()
        seen = seen | {key}
        if isinstance(key, tuple) and len(key) > 2:
            bases = self._get((key[0], key[1]), seen)
            if not bases:
                return set()
            key = key[2:]
            # Return the union of all the set from all the (base, key)
            return set.union(*[self._get(self._new_taint_key(b, key), seen) for b in bases])
        else:
            return self._taints.get(key, set())

    @staticmethod
    def _new_taint_key(b, key):
        return (b, *key) if isinstance(key, tuple) else (b, key)

    def set(self, key, value):
        if isinstance(key, tuple) and len(key) > 2:
            raise Exception(f'Invalid set key {[str(k) for k in key]} ')

        self._taints[key] = value

    def union(self, key, value):
        if isinstance(key, tuple) and len(key) > 2:
            raise Exception(f'Invalid set key {[str(k) for k in key]} ')
        self._taints[key] |= value

    # @property
    # def accesses(self):
    #     return self._access
    #
    # def add_access(self, key, value):
    #     self._access[key] |= {value}

    def items(self):
        """

        :return:
        """
        return self._taints.items()
        # return [(k, self._taints.get(k)) for k in self._taints.keys()]


def compute_dependency(slither):
    slither.context[KEY_INPUT] = set()
    slither.context[KEY_INPUT_SSA] = set()

    for contract in slither.contracts:
        compute_dependency_contract(contract, slither)


def compute_dependency_contract(contract, slither):
    if KEY_SSA in contract.context:
        return

    contract.context[KEY_SSA] = Taint()  # defaultdict(set)
    contract.context[KEY_SSA_UNPROTECTED] = Taint()  # defaultdict(set)
    contract.context[KEY_ACCESS_NON_SSA] = defaultdict(set)
    contract.context[KEY_ACCESS_SSA] = defaultdict(set)

    for function in contract.all_functions_called:
        compute_dependency_function(function)

        propagate_function(contract,
                           function,
                           KEY_SSA,
                           KEY_NON_SSA)

        propagate_function(contract,
                           function,
                           KEY_SSA_UNPROTECTED,
                           KEY_NON_SSA_UNPROTECTED)

        # pprint_dependency(function)

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
        contract.context[context_key].union(key, set(values))


#    contract.context[context_key_non_ssa] |= convert_to_non_ssa(data_depencencies)

def _get_taints(key, seen, taints):
    """
    This is only used if "key" is a triplet. The function will go recursively to find out the elements
    points by the triplet. We could simplify this to just better handle this corner case
    :param key:
    :param seen:
    :param taints:
    :return:
    """
    if isinstance(key, Constant):
        return set()
    if key in seen:
        return set()
    seen = seen | {key}
    if isinstance(key, tuple) and len(key) > 2:
        bases = _get_taints((key[0], key[1]), seen, taints)
        if not bases:
            return set()
        key = key[2:]
        # Return the union of all the set from all the (base, key)
        return set.union(*[_get_taints(_new_taint_key(b, key), seen, taints) for b in bases])
    else:
        return taints.get(key, set())


# @staticmethod
def _new_taint_key(b, key):
    return (b, *key) if isinstance(key, tuple) else (b, key)


def transitive_close_dependencies(context, context_key, context_key_non_ssa):
    # transitive closure
    changed = True
    while changed:
        changed = False
        # Need to create new set() as its changed during iteration
        data_depencencies = {k: set([v for v in values]) for k, values in context.context[context_key].items()}
        for key, items in data_depencencies.items():
            for item in items:
                additional_items = context.context[context_key].get(item)
                for additional_item in additional_items:
                    if additional_item not in items and additional_item != key:
                        changed = True
                        context.context[context_key].union(key, {additional_item})
                if not additional_items and isinstance(item, tuple) and len(item) > 2:
                    additional_items = _get_taints(item, set(), context.context[context_key].taints)
                    for additional_item in additional_items:
                        if additional_item not in items and additional_item != key:
                            changed = True
                            context.context[context_key].union(key, {additional_item})
    context.context[context_key_non_ssa] = convert_to_non_ssa(context.context[context_key])


def transitive_close_node_dependencies(node, context_key):
    # transitive closure
    changed = True
    updated_dependencies = False

    if context_key not in node.context:
        node.context[context_key] = Taint()  # defaultdict(set)

    while changed:
        changed = False
        # Need to create new set() as its changed during iteration
        data_depencencies = {k: set([v for v in values]) for k, values in node.context[context_key].items()}

        if node.fathers:
            for father in node.fathers:
                for key, items in father.context[context_key].items():
                    if key not in node.context[context_key].taints:
                        changed = True
                        updated_dependencies = True
                        node.context[context_key].set(key, set(items))
                    for item in items:
                        if item not in node.context[context_key].get(key):
                            node.context[context_key].union(key, {item})
                            changed = True
                            updated_dependencies = True

        for key, items in data_depencencies.items():
            for item in items:
                additional_items = node.context[context_key].get(item)
                for additional_item in additional_items:
                    if additional_item not in items and additional_item != key:
                        changed = True
                        updated_dependencies = True
                        node.context[context_key].union(key, {additional_item})

                if not additional_items and isinstance(item, tuple) and len(item) > 2:
                    additional_items = _get_taints(item, set(), node.context[context_key].taints)
                    for additional_item in additional_items:
                        if additional_item not in items and additional_item != key:
                            changed = True
                            updated_dependencies = True
                            node.context[context_key].union(key, {additional_item})

    return updated_dependencies


def propagate_contract(contract, context_key, context_key_non_ssa):
    transitive_close_dependencies(contract, context_key, context_key_non_ssa)


def add_dependency(node, ir, is_protected):
    ssa = node.context[KEY_SSA]
    ssa_unprotected = node.context[KEY_SSA_UNPROTECTED]

    if isinstance(ir, PhiMemberMust):
        for key, item in ir.phi_info.items():
            key = (ir.lvalue, key)
            if isinstance(key, Constant):
                ssa.set(key, {item})
            else:
                ssa.union(key, {item})

                # _key = (ir.lvalue, TOP)
                # ssa[_key] |= {item}
            if not is_protected:
                if isinstance(key, Constant):
                    ssa_unprotected.set(key, {item})
                else:
                    ssa_unprotected.union(key, {item})

        return

        # key = (ir.lvalue, TOP)
        # ssa[key] |= {ir.base}
        # if not is_protected:
        #     ssa_unprotected[key] |= {ir.base}

    elif isinstance(ir, PhiMemberMay):
        for key, item in ir.phi_info.items():
            key = (ir.lvalue, key)
            ssa.union(key, {item})
            if not is_protected:
                ssa_unprotected.union(key, {item})

        return

        # key = (ir.lvalue, TOP)
        # ssa[key] = {ir.base}
        # if not is_protected:
        #     ssa_unprotected[key] = {ir.base}

    elif isinstance(ir, AccessMember):
        # print(ir)
        if isinstance(ir.lvalue.type, UserDefinedType) and isinstance(ir.lvalue.type.type, Structure):
            members = ir.lvalue.type.type.elems.values()
            for member in members:
                key = (ir.lvalue, Constant(member.name))
                elem = (ir.variable_left, ir.variable_right, Constant(member.name))
                ssa.set(key, {elem})

                node.function.contract.context[KEY_ACCESS_SSA][elem] |= {key}

                key_non_ssa = (convert_variable_to_non_ssa(ir.lvalue), Constant(member.name))
                elem_non_ssa = (convert_variable_to_non_ssa(ir.variable_left),
                                convert_variable_to_non_ssa(ir.variable_right),
                                Constant(member.name))
                node.function.contract.context[KEY_ACCESS_NON_SSA][elem_non_ssa] |= {key_non_ssa}

                if not is_protected:
                    ssa_unprotected.set(key, {elem})

        else:
            key = ir.lvalue
            ssa.set(key, {(ir.variable_left, ir.variable_right)})
            if not is_protected:
                ssa_unprotected.set(key, {(ir.variable_left, ir.variable_right)})

        return

    elif isinstance(ir, Index):
        # key = (ir.lvalue, ir.variable_right)
        key = ir.lvalue
        ssa.set(key, {(ir.variable_left, ir.variable_right)})
        if not is_protected:
            ssa_unprotected.set(key, {(ir.variable_left, ir.variable_right)})

        return

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
    if isinstance(ir, Phi) and isinstance(ir.lvalue.type, UserDefinedType) and isinstance(ir.lvalue.type.type,
                                                                                          Structure):
        members = ir.lvalue.type.type.elems.values()
        for member in members:
            key = (ir.lvalue, Constant(member.name))
            [ssa.union(key, {(v, Constant(member.name))}) for v in read]
            if not is_protected:
                [ssa_unprotected.union(key, {(v, Constant(member.name))}) for v in read]

    else:
        [ssa.union(key, {v}) for v in read if (not isinstance(v, (Constant, MemberVariable, IndexVariable)))]
        [ssa.union(key, {(v.base, v.member)}) for v in read if (isinstance(v, MemberVariable))]
        [ssa.union(key, {(v.base, v.offset)}) for v in read if isinstance(v, IndexVariable)]

        if not is_protected:
            [ssa_unprotected.union(key, {v}) for v in read if
             not isinstance(v, (Constant, MemberVariable, IndexVariable))]
            [ssa_unprotected.union(key, {(v.base, v.member)}) for v in read if isinstance(v, MemberVariable)]
            [ssa_unprotected.union(key, {(v.base, v.offset)}) for v in read if isinstance(v, IndexVariable)]


def compute_dependency_node(node, is_protected):
    if not node:
        return
    if KEY_SSA in node.context:
        return

    node.context[KEY_SSA] = Taint()  # defaultdict(set)
    node.context[KEY_SSA_UNPROTECTED] = Taint()  # defaultdict(set)
    node.context[KEY_ACCESS_NON_SSA] = defaultdict(set)
    node.context[KEY_ACCESS_SSA] = defaultdict(set)

    for ir in node.irs_ssa:
        if isinstance(ir, OperationWithLValue) and ir.lvalue:
            add_dependency(node, ir, is_protected)

    for dom in node.dominance_exploration_ordered:
        compute_dependency_node(dom, is_protected)


def compute_dependency_function(function):
    if KEY_SSA in function.context:
        return

    function.context[KEY_SSA] = Taint()  # defaultdict(set)
    function.context[KEY_SSA_UNPROTECTED] = Taint()  # defaultdict(set)
    function.context[KEY_ACCESS_NON_SSA] = defaultdict(set)
    function.context[KEY_ACCESS_SSA] = defaultdict(set)

    is_protected = function.is_protected()

    compute_dependency_node(function.entry_point, is_protected)

    nodes = function.nodes_ordered_dominators

    while nodes:
        node = nodes[0]

        nodes = nodes[1:]
        if transitive_close_node_dependencies(node, KEY_SSA):
            nodes.append(node)
        else:
            node.context[KEY_NON_SSA] = convert_to_non_ssa(node.context[KEY_SSA].taints)
        if transitive_close_node_dependencies(node, KEY_SSA_UNPROTECTED):
            if node not in nodes:
                nodes.append(node)
        else:
            node.context[KEY_NON_SSA_UNPROTECTED] = convert_to_non_ssa(node.context[KEY_SSA_UNPROTECTED].taints)

    nodes_end = [node for node in function.nodes if node.will_return]

    nodes = [x for x in nodes_end]

    if nodes:
        initial_node = nodes[0]
        nodes = nodes[1:]
        initial_context = initial_node.context
        ssa = initial_context[KEY_SSA]
        ssa_unprotected = initial_context[KEY_SSA_UNPROTECTED]

        non_ssa = convert_to_non_ssa(ssa)
        non_ssa_unprotected = convert_to_non_ssa(ssa_unprotected)

        for other_node in nodes:
            other_context = other_node.context
            for key, items in other_context[KEY_SSA].items():
                ssa.union(key, items)
            for key, items in other_context[KEY_SSA_UNPROTECTED].items():
                ssa_unprotected.union(key, items)

            for key, items in convert_to_non_ssa(other_context[KEY_SSA]).items():
                non_ssa.union(key, items)
            for key, items in convert_to_non_ssa(other_context[KEY_SSA_UNPROTECTED]).items():
                non_ssa_unprotected.union(key, items)

    else:
        ssa = Taint()  # defaultdict(set)
        ssa_unprotected = Taint()  # defaultdict(set)
        non_ssa = Taint()  # defaultdict(set)
        non_ssa_unprotected = Taint()  # defaultdict(set)

    function.context[KEY_SSA] = ssa
    function.context[KEY_SSA_UNPROTECTED] = ssa_unprotected
    function.context[KEY_NON_SSA] = non_ssa
    function.context[KEY_NON_SSA_UNPROTECTED] = non_ssa_unprotected


def convert_variable_to_non_ssa(v):
    if isinstance(v, (LocalIRVariable, StateIRVariable, TemporaryVariableSSA,
                      IndexVariableSSA, TupleVariableSSA, MemberVariableSSA)):
        return v.non_ssa_version
    if isinstance(v, tuple) and len(v) >= 2:
        base = v[0]
        if isinstance(base, SolidityVariable):
            return tuple([base] + list(v[1:]))
        else:
            return tuple([base.non_ssa_version] + list(v[1:]))
    assert isinstance(v, (Constant, SolidityVariable, Contract, Enum, SolidityFunction, Structure, Function, Type))
    return v


def _get_index(v):
    if isinstance(v, tuple):
        return v[0].index
    return v.index


def convert_to_non_ssa(data_dependencies):
    # Need to create new set() as its changed during iteration
    ret = defaultdict(set)
    for (k, values) in data_dependencies.items():
        # if isinstance(k, tuple) and len(k) > 2:
        #    continue
        var = convert_variable_to_non_ssa(k)
        ret[var] |= set([convert_variable_to_non_ssa(v) for v in values])
        # ret[var] |= set([convert_variable_to_non_ssa(v) for v in values if not (isinstance(v, tuple) and len(v) > 2)])

    return Taint(ret)
