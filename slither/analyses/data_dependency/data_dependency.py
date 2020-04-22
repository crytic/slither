"""
    Compute the data depenency between all the SSA variables
"""
from collections import defaultdict, namedtuple
from typing import Union, Set, Dict, List, Tuple, ItemsView, Optional

from prettytable import PrettyTable

from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import (Contract, Enum, Function,
                                       SolidityFunction, SolidityVariable,
                                       SolidityVariableComposed, Structure)
from slither.core.solidity_types import UserDefinedType, ArrayType, MappingType
from slither.core.solidity_types.type import Type
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.structure_variable import StructureVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations import Index, OperationWithLValue, InternalCall, PhiMemberMust, PhiMemberMay, \
    AccessMember, Phi, Balance, Assignment
from slither.slithir.variables import (Constant, LocalIRVariable,
                                       IndexVariable, IndexVariableSSA,
                                       StateIRVariable, MemberVariable, MemberVariableSSA,
                                       TemporaryVariableSSA, TupleVariableSSA, TemporaryVariable)
from slither.slithir.variables.variable import SlithIRVariable

VariableKey = Union[Variable, Tuple[Variable, Constant]]
Dependencies = Set[VariableKey]


###################################################################################
###################################################################################
# region User APIs
###################################################################################
###################################################################################

class Access:

    def __init__(self, base: Variable, members: Union[List, Tuple]):
        self._base = base
        self._members = members

    def __str__(self):
        return f'{self._base}.' + '.'.join([f'{x}' for x in list(self._members)])

    def to_tuple(self) -> Tuple:
        return (self._base,) + tuple(self._members)


def _to_tuple(l, n):
    return tuple(list(l) + [n])


def is_dependent(variable: Union[Variable, Tuple, Access],
                 source: Union[Variable, Tuple],
                 context: Union[Contract, Function, Node],
                 only_unprotected=False):
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
    if isinstance(variable, Access):
        variable = variable.to_tuple()
    if isinstance(source, Access):
        source = source.to_tuple()
    context = context.context

    graph: Graph
    if only_unprotected:
        graph = context[KEY_GRAPH_ONLY_UNPROTECTED]
    else:
        graph = context[KEY_GRAPH]
    return graph.is_dependent(variable, source, False)


def is_dependent_ssa(variable: Union[Variable, Tuple],
                     source: Union[Variable, Tuple],
                     context: Union[Contract, Function, Node],
                     only_unprotected=False):
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

    graph: Graph
    if only_unprotected:
        graph = context[KEY_GRAPH_ONLY_UNPROTECTED]
    else:
        graph = context[KEY_GRAPH]
    return graph.is_dependent(variable, source, True)


GENERIC_TAINT = {SolidityVariableComposed('msg.sender'),
                 SolidityVariableComposed('msg.value'),
                 SolidityVariableComposed('msg.data'),
                 SolidityVariableComposed('tx.origin')}


def is_tainted(variable: Union[Variable, Tuple],
               context: Union[Contract, Function, Node],
               only_unprotected=False, ignore_generic_taint=False):
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


def is_tainted_ssa(variable: Union[Variable, Tuple],
                   context: Union[Contract, Function, Node],
                   only_unprotected=False, ignore_generic_taint=False):
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


def get_dependencies(
        variable: Union[Variable, Tuple],
        context: Union[Contract, Function, Node],
        only_unprotected: bool = False) -> Set[Variable]:
    """
    Return the variables for which `variable` depends on.

    :param variable: The target
    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: set(Variable)
    """
    assert isinstance(context, (Contract, Function, Node))
    assert isinstance(only_unprotected, bool)
    graph: Graph
    if only_unprotected:
        graph = context.context[KEY_GRAPH_ONLY_UNPROTECTED]
    else:
        graph = context.context[KEY_GRAPH]
    return graph.get_dependencies(variable, is_ssa=False)


def get_all_dependencies(
        context: Union[Contract, Function, Node],
        only_unprotected: bool = False) -> Dict[Variable, Set[Variable]]:
    """
    Return the dictionary of dependencies.

    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: Dict(Variable, set(Variable))
    """
    assert isinstance(context, (Contract, Function, Node))
    if only_unprotected:
        return context.context[KEY_NON_SSA_UNPROTECTED]
    return context.context[KEY_NON_SSA]


def get_dependencies_ssa(
        variable: Union[Variable, Tuple],
        context: Union[Contract, Function, Node],
        only_unprotected: bool = False) -> Set[Variable]:
    """
    Return the variables for which `variable` depends on (SSA version).

    :param variable: The target (must be SSA variable)
    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: set(Variable)
    """
    assert isinstance(context, (Contract, Function, Node))
    if only_unprotected:
        graph = context.context[KEY_GRAPH_ONLY_UNPROTECTED]
    else:
        graph = context.context[KEY_GRAPH]
    return graph.get_dependencies(variable, is_ssa=True)


def get_all_dependencies_ssa(
        context: Union[Contract, Function, Node],
        only_unprotected: bool = False) -> Dict[Variable, Set[Variable]]:
    """
    Return the dictionary of dependencies.

    :param context: Either a function (interprocedural) or a contract (inter transactional)
    :param only_unprotected: True if consider only protected functions
    :return: Dict(Variable, set(Variable))
    """
    assert isinstance(context, (Contract, Function))
    if only_unprotected:
        return context.context[KEY_SSA_UNPROTECTED]
    return context.context[KEY_SSA]


# endregion
###################################################################################
###################################################################################
# region Module constants
###################################################################################
###################################################################################

KEY_SSA = "DATA_DEPENDENCY_SSA"
KEY_NON_SSA = "DATA_DEPENDENCY"

KEY_SSA_UNPROTECTED = "DATA_DEPENDENCY_SSA_UNPROTECTED"
KEY_NON_SSA_UNPROTECTED = "DATA_DEPENDENCY_UNPROTECTED"

KEY_INPUT = "DATA_DEPENDENCY_INPUT"
KEY_INPUT_SSA = "DATA_DEPENDENCY_INPUT_SSA"

KEY_GRAPH = "KEY_GRAPH_DEPENDENCY"
KEY_GRAPH_ONLY_UNPROTECTED = "KEY_GRAPH_DEPENDENCY_UNPROTECTED"


# endregion
###################################################################################
###################################################################################
# region PrettyPrint TODO: clean these functions
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


def _get_dependencies(v, c, is_ssa):
    if is_ssa:
        return get_dependencies_ssa(v, c)
    return get_dependencies(v, c)


def _get(v, c, is_ssa):
    return list(set([_convert(d) for d in _get_dependencies(v, c, is_ssa) if not isinstance(d, (TemporaryVariable,
                                                                                                IndexVariable,
                                                                                                MemberVariable,
                                                                                                tuple))]))


def _add_row_rec_structure(v: Variable,
                           members,
                           c: Union[Contract, Function, Node],
                           key: str,
                           table: PrettyTable,
                           is_ssa: bool):
    for elem in members:
        deps = []
        for dep in _get_dependencies((v, elem.name), c, is_ssa):
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


def _add_row_rec(v: Union[Variable, Tuple],
                 c: Union[Contract, Function, Node],
                 key: str,
                 table: PrettyTable,
                 is_ssa: bool):
    if isinstance(v, tuple):
        deps = []
        for dep in _get_dependencies(v, c, is_ssa):
            # if (isinstance(elem.type, UserDefinedType) and isinstance(elem.type.type, Structure) or
            #         isinstance(elem.type, (ArrayType, MappingType))):
            #     _add_row_rec(dep, c, f'{key}.{elem}', table, is_ssa)
            # else:
            if isinstance(dep, tuple):
                deps.append(str((str(dep[0]), str(dep[1]))))
            else:
                deps.append(str(dep))
        if deps:
            table.add_row([f'{key}.{v[0]}.{v[1]}',
                           str(deps),
                           is_tainted((key, v), c)])

    # Structure
    elif _is_structure(v.type):
        _add_row_rec_structure(
            v,
            v.type.type.elems.values(),
            c,
            key,
            table,
            is_ssa
        )

    else:
        # Mapping to structure
        st = _points_to_structure(v)
        if st:
            _add_row_rec_structure(
                v,
                st.elems.values(),
                c,
                key,
                table,
                is_ssa
            )
        else:
            table.add_row([str(v), _get(v, c, is_ssa), is_tainted(v, c)])


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

    table.add_row(['#####', 'NON SSA', '####'])

    context = c.context[KEY_NON_SSA]

    for k, values in context.items():
        values = str([_convert_string(v) for v in values])
        if isinstance(k, tuple):
            table.add_row([str([[str(kk) for kk in k]]), values, is_tainted(k, c)])
        else:
            table.add_row([str(k), values, is_tainted(k, c)])


def unroll(pointer, base):
    ret = []
    if _is_structure(pointer.type):
        for member_name, member in pointer.type.type.elems.items():
            ret += unroll(member, base + [member_name])
    else:
        st = _points_to_structure(pointer)
        if st:
            for member_name, member in st.elems.items():
                ret += unroll(member, base + [member_name])
        else:
            ret = tuple([base])
    return ret


def pprint_dependency_table(context):
    table = PrettyTable(['Variable', 'Dependencies', 'Is tainted'])

    if isinstance(context, Contract):
        for v in context.state_variables:
            unrolled_variables = unroll(v, [v])
            for v in unrolled_variables:
                table.add_row([_tmp_to_str(tuple(v)),
                               [_tmp_to_str(x) for x in get_dependencies(tuple(v), context, False)],
                               False])

    if isinstance(context, Function):
        for v in context.contract.state_variables + context.local_variables + context.parameters + context.returns:
            unrolled_variables = unroll(v, [v])
            for v in unrolled_variables:
                table.add_row([_tmp_to_str(tuple(v)),
                               [_tmp_to_str(x) for x in get_dependencies(tuple(v), context, False)],
                               False])

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
            self._taints: Dict[VariableKey, Dependencies] = defaultdict(set)
        else:
            self._taints = taints

    @property
    def taints(self) -> Dict[VariableKey, Dependencies]:
        """

        :return:
        """
        return self._taints

    def get_dependencies(self, key: VariableKey) -> Dependencies:
        """

        :param key:
        :return:
        """
        return self._taints.get(key, set())
        # return self._get(key, set())

    def _get_all_deps(self, key, seen) -> Set:
        if isinstance(key, Constant):
            return set()
        if key in seen:
            return set()
        seen = seen | {key}
        if isinstance(key, tuple) and len(key) > 2:
            bases = self._get_all_deps((key[0], key[1]), seen)
            if not bases:
                return set()
            key = key[2:]
            # Return the union of all the set from all the (base, key)
            return set.union(*[self._get_all_deps(self._new_taint_key(b, key), seen) for b in bases])
        else:
            return self._taints.get(key, set())

    def _get_all_root(self, elem: Union[Variable, Tuple], accesses):
        if isinstance(elem, (tuple, list)) and len(elem) >= 2:
            next_level = {elem[0:2]}
            sts = elem[2:]
            for st in sts:
                level = set(next_level)
                next_level = set()
                for l in level:
                    k = _to_tuple(l, st)
                    next_level |= accesses[k]
            return {tuple(list(n)) for n in next_level}
        return {elem}

    def is_dependent(self, variable: VariableKey, source: VariableKey, accesss):

        variables = self._get_all_deps(variable, set())
        sources = self._get_all_root(source, accesss)

        return any((v in sources for v in variables))

    @staticmethod
    def _new_taint_key(b, key):
        return (b, *key) if isinstance(key, tuple) else (b, key)

    def set_dependencies(self, key: VariableKey, value: Dependencies):
        if isinstance(key, tuple) and len(key) > 2:
            raise Exception(f'Invalid set key {[str(k) for k in key]} ')

        self._taints[key] = value

    def union(self, key: VariableKey, value: Dependencies):
        if isinstance(key, tuple) and len(key) > 2:
            raise Exception(f'Invalid set key {[str(k) for k in key]} ')
        self._taints[key] |= value

    # @property
    # def accesses(self):
    #     return self._access
    #
    # def add_access(self, key, value):
    #     self._access[key] |= {value}

    def items(self) -> ItemsView[VariableKey, Dependencies]:
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
    if KEY_GRAPH in contract.context:
        return

    contract.context[KEY_GRAPH] = Graph()
    contract.context[KEY_GRAPH_ONLY_UNPROTECTED] = Graph()

    for function in contract.functions + contract.modifiers:
        compute_dependency_function(function)

        contract.context[KEY_GRAPH].union(function.context[KEY_GRAPH])
        contract.context[KEY_GRAPH_ONLY_UNPROTECTED].union(function.context[KEY_GRAPH_ONLY_UNPROTECTED])

        if function.visibility in ['public', 'external']:
            [slither.context[KEY_INPUT].add(p) for p in function.parameters]
            [slither.context[KEY_INPUT_SSA].add(p) for p in function.parameters_ssa]


def propagate_function(contract, function, context_key, context_key_non_ssa):
    # transitive_close_dependencies(function, context_key, context_key_non_ssa)
    # Propage data dependency
    data_depencencies = function.context[context_key]

    for (key, values) in data_depencencies.items():
        contract.context[context_key].union(key, set(values))


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
                additional_items = context.context[context_key].get_dependencies(item)
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
                        node.context[context_key].set_dependencies(key, set(items))
                    for item in items:
                        if item not in node.context[context_key].get_dependencies(key):
                            node.context[context_key].union(key, {item})
                            changed = True
                            updated_dependencies = True

        for key, items in data_depencencies.items():
            for item in items:
                additional_items = node.context[context_key].get_dependencies(item)
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


def _is_structure(type: Type):
    return isinstance(type, UserDefinedType) and isinstance(type.type, Structure)


def _points_to_structure(variable) -> Optional[Structure]:
    if isinstance(variable.type, MappingType):
        if _is_structure(variable.type.type_to):
            return variable.type.type_to.type
    if isinstance(variable.type, ArrayType):
        if _is_structure(variable.type.type):
            return variable.type.type.type
    return None


def _tmp_to_str(k: VariableKey):
    if isinstance(k, tuple):
        return '.'.join([_tmp_to_str(x) for x in k])
    return str(k)


Edge = namedtuple('Edge', ['source', 'destination', 'step'])


def _convert_edge_to_non_ssa(edge: Edge):
    return Edge(convert_variable_to_non_ssa(edge.source),
                convert_variable_to_non_ssa(edge.destination),
                convert_variable_to_non_ssa(edge.step) if edge.step else None)


class Graph:

    def __init__(self,
                 edges: Optional[List[Edge]] = None,
                 nodes: Optional[Dict[VariableKey, List[Edge]]] = None,
                 edges_non_ssa: Optional[List[Edge]] = None,
                 nodes_non_ssa: Optional[Dict[VariableKey, List[Edge]]] = None):
        self._edges: List[Edge] = [] if edges is None else edges
        self._nodes: Dict[VariableKey, List[Edge]] = defaultdict(list) if nodes is None else nodes

        self._edges_non_ssa: List[Edge] = [] if edges_non_ssa is None else edges_non_ssa
        self._nodes_non_ssa: Dict[VariableKey, List[Edge]] = defaultdict(
            list) if nodes_non_ssa is None else nodes_non_ssa

    @property
    def edges(self) -> List[Edge]:
        return self._edges

    @property
    def nodes(self) -> Dict[VariableKey, List[Edge]]:
        return self._nodes

    @property
    def edges_non_ssa(self) -> List[Edge]:
        return self._edges_non_ssa

    @property
    def nodes_non_ssa(self) -> Dict[VariableKey, List[Edge]]:
        return self._nodes_non_ssa

    def clone(self) -> "Graph":
        return Graph(
            list(self._edges),
            dict(self._nodes),
            list(self._edges_non_ssa),
            dict(self._nodes_non_ssa)
        )

    def union(self, graph: "Graph"):
        self._edges += graph.edges
        self._edges_non_ssa += graph.edges_non_ssa
        for k, values in graph.nodes.items():
            self._nodes[k] += values
        for k, values in graph.nodes_non_ssa.items():
            self._nodes_non_ssa[k] += values

    def convert_to_non_ssa(self):
        for edge in self._edges:
            self._edges_non_ssa.append(_convert_edge_to_non_ssa(edge))

        for key, edges in self._nodes.items():
            for edge in edges:
                self._nodes_non_ssa[convert_variable_to_non_ssa(key)].append(_convert_edge_to_non_ssa(edge))

    def add_edge(self, src, dst):
        if isinstance(dst, tuple) and isinstance(dst[0], IndexVariable):
            if isinstance(src, tuple) and src[1] == dst[1]:
                edge = Edge(src[0], dst[0], None)
                self._edges.append(edge)
                self._nodes[src[0]].append(edge)
                return
        if isinstance(src, tuple):
            edge = Edge(src[0], dst, src[1])
            self._edges.append(edge)
            self._nodes[src[0]].append(edge)
        else:
            edge = Edge(src, dst, None)
            self._edges.append(edge)
            self._nodes[src].append(edge)

    def is_dependent(self, variable: VariableKey, source: VariableKey, is_ssa: bool) -> bool:
        return self._is_subgraph(variable, source, [], [], set(), is_ssa)

    def _is_subgraph(self, variable, candidate, candidate_to_explore, to_explore: List, explored: Set,
                     is_ssa: bool) -> bool:
        """
        Check if candidate is a subgraph of variable
        :param variable:
        :param candidate:
        :param candidate_to_explore:
        :param to_explore:
        :param explored:
        :param is_ssa:
        :return:
        """
        if (variable, tuple(candidate_to_explore), tuple(to_explore)) in explored:
            return False
        if not candidate_to_explore:
            candidate_to_explore = candidate
        if not isinstance(candidate_to_explore, (tuple, list)):
            candidate_to_explore = [candidate_to_explore]
        if [variable] == candidate_to_explore:
            return True
        if [variable] == candidate:
            return True
        explored.add((variable, tuple(candidate_to_explore), tuple(to_explore)))
        # explored = explored | {variable}
        if isinstance(variable, (tuple, list)):
            base = variable[0]
            next = list(variable[1:]) + to_explore
        else:
            base = variable
            next = to_explore

        ret = False
        if isinstance(candidate, (tuple, list)) and [base] + next == list(candidate):
            return True
        base_candidate = candidate_to_explore[0]
        next_candidate = candidate_to_explore[1:]

        for edge in self._nodes[base] if is_ssa else self._nodes_non_ssa[base]:
            if not edge.step:
                ret |= self._is_subgraph(edge.destination, candidate, candidate_to_explore, next, explored, is_ssa)
            if edge.step and next:
                if edge.source == base_candidate:
                    if not next_candidate:
                        return True
                    if edge.step == next_candidate[0]:
                        ret |= self._is_subgraph(edge.destination, candidate, next_candidate[1:], next[1:], explored,
                                                 is_ssa)
                if edge.step == base_candidate and next_candidate:
                    if edge.step == next[0]:
                        ret |= self._is_subgraph(edge.destination, candidate, next_candidate, next[1:], explored,
                                                 is_ssa)
                    else:
                        ret |= self._is_subgraph(edge.destination, candidate, next_candidate, next, explored, is_ssa)
                if edge.step == next[0]:
                    ret |= self._is_subgraph(edge.destination, candidate, candidate_to_explore, next[1:], explored,
                                             is_ssa)
        return ret

    def _extract(self, edge: List[VariableKey]):
        # candidate: [ variable, [ constant]]
        candidates: List[Tuple[VariableKey, List[VariableKey]]] = []
        for idx, e in enumerate(edge):
            if not isinstance(e, (SlithIRVariable, Constant, str)):
                candidates.append((e, edge[idx + 1:]))
        ret = []
        for candidate, potential_members in candidates:
            valid_members = []
            pointer = candidate
            is_valid = True
            for member in potential_members:
                if _is_structure(pointer.type):
                    if member in pointer.type.type.elems:
                        valid_members.append(member)
                        pointer = pointer.type.type.elems[member]
                    else:
                        is_valid = False
                        break
                else:
                    st = _points_to_structure(pointer)
                    print(f'St: {st}')
                    if st:
                        if member in st.elems:
                            valid_members.append(member)
                            pointer = st.elems[member]
                        else:
                            is_valid = False
                            break
                    else:
                        is_valid = True
                        break
            if _is_structure(pointer.type) or _points_to_structure(pointer):
                is_valid = False
            if is_valid:
                ret.append([candidate] + valid_members)
        return ret

    def get_dependencies(self, variable, is_ssa: bool):

        # TODO : hack, the first condition should ge better handle
        # this happen if the variable is not at all in the node
        if isinstance(variable, (tuple, list)):
            base = variable[0]
        else:
            base = variable

        nodes = self._nodes if is_ssa else self._nodes_non_ssa
        if base not in nodes:
            return set()

        leaves_, edges = self._get(variable, [], set(), is_ssa, [])
        leaves = set()

        for leave in leaves_:
            if isinstance(leave, (tuple, list)):
                extracted = self._extract(leave)
                for extract in extracted:
                    leaves.add(tuple(extract))
            else:
                leaves.add(leave)
        edges = set(tuple(i) for i in edges)
        for edge in edges:
            extracts = self._extract(edge)
            for extracted in extracts:
                leaves.add(tuple(extracted))
        return leaves

    def _get(self, variable, to_explore: List, explored: Set, is_ssa: bool, edges_steps) -> Tuple[Set, List]:
        """
        Return the leaves
        :param variable:
        :param to_explore:
        :param explored:
        :param is_ssa:
        :return:
        """
        if variable in explored:
            return set(), [edges_steps]
        explored = explored | {variable}
        if isinstance(variable, (tuple, list)):
            base = variable[0]
            next = list(variable[1:]) + to_explore
        else:
            base = variable
            next = to_explore
        ret = set()
        edges_steps_ret = []

        for edge in self._nodes[base] if is_ssa else self._nodes_non_ssa[base]:
            if not edge.step:
                if isinstance(edge.source, (LocalVariable, StateVariable)):
                    edges_steps = [edge.source]
                ret_set, ret_edges = self._get(edge.destination, next, explored, is_ssa, edges_steps)
                ret |= ret_set
                edges_steps_ret += ret_edges
            elif edge.step:
                if next and edge.step == next[0]:
                    if isinstance(edge.source, (LocalVariable, StateVariable)):
                        edges_steps = [edge.source]
                    ret_set, ret_edges = self._get(edge.destination,
                                                   next[1:],
                                                   explored,
                                                   is_ssa,
                                                   edges_steps + [edge.step])
                    ret |= ret_set
                    edges_steps_ret += ret_edges
        if ret:
            return ret, edges_steps_ret
        if isinstance(variable, SlithIRVariable):
            return set(), [edges_steps]
        return {variable}, [edges_steps]

    def to_dot(self):
        print(f'digraph SSA{{')
        for edge in self._edges:
            if edge.step:
                print(f'\t\t"{_tmp_to_str(edge.source)}" -> "{_tmp_to_str(edge.destination)}" [label="{edge.step}"];')
            else:
                print(f'\t\t"{_tmp_to_str(edge.source)}" -> "{_tmp_to_str(edge.destination)}";')
        print('}')

        print(f'digraph NONSSA{{')
        for edge in self._edges_non_ssa:
            if edge.step:
                print(f'\t\t"{_tmp_to_str(edge.source)}" -> "{_tmp_to_str(edge.destination)}" [label="{edge.step}"];')
            else:
                print(f'\t\t"{_tmp_to_str(edge.source)}" -> "{_tmp_to_str(edge.destination)}";')
        print('}')


def _set_dependencies(key: VariableKey, deps: Dependencies, graph: Graph):
    for dep in deps:
        graph.add_edge(key, dep)


def _propagate_structure(phi_info: Dict[Variable, Variable],
                         all_members: List[StructureVariable],
                         lvalue: Variable,
                         base: Union[Variable, Tuple[Variable]],
                         graph: Graph):
    for key_info, item in phi_info.items():
        # key_info can only be a constant for Structure
        assert isinstance(key_info, Constant)
        key = (lvalue, key_info)
        _set_dependencies(key, {item}, graph)

    # Convert StructureVariable to Constant
    member_not_updated = [Constant(m.name) for m in all_members if Constant(m.name) not in phi_info.keys()]
    for member in member_not_updated:
        key = (lvalue, member)
        if isinstance(base, tuple):
            item_base = base + (member,)
        else:
            item_base = (base, member)
        _set_dependencies(key, {item_base}, graph)


def add_dependency(node, ir):
    graph = node.function.context[KEY_GRAPH]

    if isinstance(ir, PhiMemberMust) and _is_structure(ir.lvalue.type):
        # For PhiMust on structure:
        # Update all the (member, item) from phi_info -> lvalue.member = item
        # And for the member not updated -> lvalue.member = base.member
        _propagate_structure(ir.phi_info,
                             ir.lvalue.type.type.elems.values(),
                             ir.lvalue,
                             ir.base,
                             graph)

        return

    # Mapping / array
    # We dont use _key_info for mapping/array, and merge all the cells together
    elif isinstance(ir, PhiMemberMust) or (isinstance(ir, PhiMemberMay) and not _is_structure(ir.lvalue.type)):
        key = ir.lvalue
        # For PhiMust/May on mapping/array:
        # If points to a structure:
        #     For each (offset, item) in phi_info
        #       for each member of map[]
        #           map.member |= item.member
        # Else
        #    For each (offset, item) in phi_info
        #       map |= item
        #    map |= ir.base
        st = _points_to_structure(ir.lvalue)
        if st:
            members = st.elems.values()

            # For PhiMemberMust on a length
            # arr_2(St[]) := ϕMust(arr_1:length :-> x_1)
            # We do not propate the member, we just update the array to be dependant of the previous array
            update_length = False

            for key, base in ir.phi_info.items():
                if key == 'length':
                    update_length = True
                    continue
                _propagate_structure(dict(),
                                     members,
                                     ir.lvalue,
                                     base,
                                     graph)
            if update_length:
                _set_dependencies(ir.lvalue, {ir.base}, graph)
            return

        else:
            for item in ir.phi_info.values():
                _set_dependencies(key,
                                  {item},
                                  graph)

            _set_dependencies(key,
                              {ir.base},
                              graph)
            return

    elif isinstance(ir, PhiMemberMay):
        key_info: Constant
        for key_info, item in ir.phi_info.items():
            key = (ir.lvalue, key_info)
            _set_dependencies(key,
                              {item},
                              graph)

        return

    elif isinstance(ir, AccessMember):

        # Member_0 = Access(var, member)
        if _is_structure(ir.lvalue.type):
            # If member_0 is a structure
            # We need to update all its fields, ie
            #  Member_0.a = var.member.a
            #  Member_0.b = var.member.b
            #  Member_0.c = var.member.c
            members = ir.lvalue.type.type.elems.values()
            base: Tuple[Variable, ...] = (ir.variable_left, ir.variable_right)
            _propagate_structure(dict(),
                                 members,
                                 ir.lvalue,
                                 base,
                                 graph)

        else:
            key = ir.lvalue
            _set_dependencies(key,
                              {(ir.variable_left, ir.variable_right)},
                              graph)

        return

    elif isinstance(ir, Index):
        # lvalue = Index(left, offset)
        # lvalue is deps from left
        # If it is a structure
        # lvalue.elem = left.elem
        #
        # Unsure if we should handle the case of points_to_structure?
        # st = _points_to_structure(ir.lvalue)
        if _is_structure(ir.lvalue.type):
            members = ir.lvalue.type.type.elems.values()

            _propagate_structure(dict(),
                                 members,
                                 ir.lvalue,
                                 ir.variable_left,
                                 graph)  # keep the previous values, as we merge all the mapping

        else:
            # only one write, no need to keep previous values? (unsure)
            key = ir.lvalue
            elem = ir.variable_left
            _set_dependencies(key,
                              {elem},
                              graph)

        return

    # structure assignement
    # Ex:
    # struct St{uint a;}
    # St st1;
    # St st2;
    # st2 = st1;
    # --> st2.a == st1.a
    elif isinstance(ir, Assignment) and _is_structure(ir.lvalue.type):
        members = ir.lvalue.type.type.elems.values()
        _propagate_structure(
            dict(),
            members,
            ir.lvalue,
            ir.rvalue,
            graph
        )

        return

    # TODO: fix Balance support
    if isinstance(ir, Balance):
        key = ir.lvalue
    elif isinstance(ir.lvalue, MemberVariable):
        key = (ir.lvalue.base, ir.lvalue.member)
    else:
        key = ir.lvalue

    if isinstance(ir, InternalCall):
        read = ir.function.return_values_ssa
    elif isinstance(ir, Balance):
        read = [(ir.value, Constant('balance'))]
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

            for v in read:
                graph.add_edge(key, (v, Constant(member.name)))
    else:

        for v in read:
            if not isinstance(v, (Constant, MemberVariable)):
                graph.add_edge(key, v)
            # TODO fix balance support
            if isinstance(v, MemberVariable) and v.member not in ['balance']:
                graph.add_edge(key, (v.base, v.member))
            if isinstance(v, MemberVariable) and v.member in ['balance']:
                graph.add_edge(key, v)


def compute_dependency_node(node, explored: Set[Node]):
    if not node:
        return
    if node in explored:
        return
    explored.add(node)

    for ir in node.irs_ssa:
        if isinstance(ir, OperationWithLValue) and ir.lvalue:
            add_dependency(node, ir)

    for dom in node.dominance_exploration_ordered:
        compute_dependency_node(dom, explored)


def compute_dependency_function(function):
    if KEY_GRAPH in function.context:
        return

    function.context[KEY_GRAPH] = Graph()

    compute_dependency_node(function.entry_point, set())

    function.context[KEY_GRAPH].convert_to_non_ssa()

    if function.is_protected():
        function.context[KEY_GRAPH_ONLY_UNPROTECTED] = Graph()
    else:
        function.context[KEY_GRAPH_ONLY_UNPROTECTED] = function.context[KEY_GRAPH].clone()


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
        var = convert_variable_to_non_ssa(k)
        ret[var] |= set([convert_variable_to_non_ssa(v) for v in values])

    return Taint(ret)
