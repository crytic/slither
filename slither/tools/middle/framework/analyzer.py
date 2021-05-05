import copy
import sys
from collections import defaultdict
from itertools import count
from typing import Dict, Any, Union, List, Tuple, DefaultDict

from slither.tools.middle.framework.function import AnalysisFunction
from slither.tools.middle.framework.strategy import ConcreteStrategy, Strategy
from slither.tools.middle.framework.util import UnionFindSymVar, InconsistentStateError
from slither.tools.middle.framework.var import SymVar
from slither.tools.middle.imports.graphivz import Digraph
from slither.tools.middle.overlay.ast.call import OverlayCall
from slither.tools.middle.overlay.ast.function import OverlayFunction
from slither.tools.middle.overlay.ast.graph import OverlayGraph
from slither.tools.middle.overlay.transform import (
    outline_all_conditionals,
    compress_all_phi_nodes,
    get_all_call_sites_in_function,
    create_hashable,
)
from slither.tools.middle.overlay.util import get_all_call_sites

from slither import Slither
from slither.core.variables.variable import Variable
from slither.slithir.operations import InternalCall, HighLevelCall
from slither.slithir.variables import Constant


class GroupAnalyzer:
    groups: List

    def __init__(self):
        self.groups = []

    def add_group(self, group):
        self.groups.append(group)

    def print_groups(self):
        for member in self.groups:
            print("{}: {}".format(member.id, member))

    def clear(self):
        self.groups.clear()

    def remove_by_id(self, analyzer_id):
        for analyzer in self.groups.copy():
            if analyzer.id == analyzer_id:
                self.groups.remove(analyzer)

    def find_by_id(self, analyzer_id):
        for analyzer in self.groups:
            if analyzer.id == analyzer_id:
                return analyzer

    def extend(self, more):
        self.groups.extend(more)


analyzer_counter = count()


class Analyzer:
    # The precomputed slither object before transformation.
    slither: Slither

    # The precomputed OverlayGraph object after transformation 1.
    overlay_graph: OverlayGraph

    # A strategy object that computes new information in a user-defined way for
    # the Analyzer. TODO: change to general strategy object later.
    strategy: ConcreteStrategy

    # A data store that manages data about variables. Union-Find allows us to
    # only hold representative SymVar nodes here.
    _symvar_data: Dict[SymVar, Any]

    # A data structure to implement Union-Find on SymVars
    symvars_union_find: UnionFindSymVar

    # A global store of all local variable to symvar mappings.
    _var_to_symvar: Dict[Any, SymVar]

    # A global store of all state variable symvar mappings.
    state_var_to_symvar: Dict[Any, SymVar]

    # Manage all the live analysis functions.
    live_functions: List[AnalysisFunction]

    # A flag to figure out if the analysis has been initialized with a root function
    _initialized: bool

    # A map that keeps track of the argument/return value equalities that should
    # be drawn. This data is a subset of what is kept in the union find store.
    drawn_equalities: DefaultDict[SymVar, List]

    # A reference to the live function that is the root of our analysis
    root: AnalysisFunction

    # A unique id number to be used for identification
    id: int

    # All the state variables used in the contract.
    state_variables: List

    def __init__(self, strategy: Strategy, program: str):
        self.slither = Slither(program)
        self.overlay_graph = OverlayGraph(self.slither)
        outline_all_conditionals(self.overlay_graph)
        compress_all_phi_nodes(self.overlay_graph)

        self.strategy = strategy
        self._symvar_data = {}
        self.live_functions = []
        self.counter = count()
        self._var_to_symvar = {}
        self.state_var_to_symvar = {}
        self.symvars_union_find = UnionFindSymVar()
        self.drawn_equalities = defaultdict(list)

        self._initialized = False
        self.root = None
        self.id = next(analyzer_counter)

        # Initialize the strategy.
        strategy.set_analysis(self)

        self.state_variables = self.slither.state_variables

    @property
    def initialized(self):
        return self._initialized

    @initialized.setter
    def initialized(self, new_value: bool):
        self._initialized = new_value

    def clear(self):
        self._symvar_data.clear()
        self.live_functions.clear()
        self.counter = count()
        self._var_to_symvar = {}
        self.symvars_union_find = UnionFindSymVar()
        self.initialized = False

        # Reset the symvar counter as well
        SymVar.counter = count()

    def get_symvar_from_id(self, symvar_id) -> SymVar:
        symvar = next(
            (x for x in self.symvars_union_find.parent.keys() if x.id == int(symvar_id)), None
        )
        if symvar is None:
            print("ERROR: no symvar with id - {}".format(symvar_id))
        else:
            return symvar

    def partial_call_all(self, function):
        for stmt in function.under.statements:
            if isinstance(stmt, OverlayCall) and not stmt.loop_continue:
                self.down_call(function, stmt)

    def add_function_object(self, function):
        self.live_functions.append(function)
        self.partial_call_all(function)
        return function

    def add_function(self, function_name: str):
        # Find a function in the overlay graph with a matching name
        func = next((x for x in self.overlay_graph.functions if x.name == function_name), None)
        if func is None:
            print("ERROR: could not find function {} to start analysis".format(function_name))
            sys.exit(-1)
        added = AnalysisFunction(func, self)

        self.add_function_object(added)

        if not self.initialized:
            self.initialized = True

        if self.root is None:
            self.root = added

        return added

    def symbolize_var(self, var, func) -> SymVar:
        """
        Introduces a new symbolic variable for the given concrete variable. Puts
        the new mapping into the global mappings. Returns the new symbolic
        variable.
        """
        symvar: SymVar = SymVar(var)
        self.symvars_union_find.make_set(symvar)

        if create_hashable(var, func) in self._var_to_symvar:
            other = self._var_to_symvar[create_hashable(var, func)]
            self.symvars_union_find.union(symvar, other)
        else:
            self._var_to_symvar[create_hashable(var, func)] = symvar
        return symvar

    def get_sym_var(self, var, func):
        return self._var_to_symvar[create_hashable(var, func)]

    def get_var_value(self, var, func):
        symvar: SymVar = self.get_sym_var(var, func)
        return self.get_sym_var_value(symvar)

    def get_var_value_or_default(self, var, func, default):
        if self.is_var_resolved(var, func):
            return self.get_var_value(var, func)
        return default

    def get_sym_var_value(self, symvar):
        rep: SymVar = self.symvars_union_find.find(symvar)
        return self._symvar_data[rep]

    def set_var_value(self, var, func, value, deduce=False):
        symvar: SymVar = self.get_sym_var(var, func)
        self.set_sym_var_value(symvar, value)
        if deduce:
            self.deduce_path_from_root(var, func)

    def set_sym_var_value(self, symvar, value):
        # Check if there is already a value for this variable.
        rep: SymVar = self.symvars_union_find.find(symvar)
        if rep in self._symvar_data and self._symvar_data[rep] != value:
            raise InconsistentStateError(
                "Trying to assign {} which has value {} to {}".format(
                    symvar, self._symvar_data[rep], value
                )
            )
        self._symvar_data[rep] = value

    def set_equal(self, a, a_func, b, b_func):
        sym_a = self.get_sym_var(a, a_func)
        sym_b = self.get_sym_var(b, b_func)

        if self.is_sym_var_resolved(sym_a) and not self.is_sym_var_resolved(sym_b):
            # Let sym_b inherit the resolved value of sym_a
            self.symvars_union_find.union(sym_b, sym_a)
        elif self.is_sym_var_resolved(sym_b) and not self.is_sym_var_resolved(sym_a):
            # Let sym_a inherit the resolved value of sym_b.
            self.symvars_union_find.union(sym_a, sym_b)
        elif self.is_sym_var_resolved(sym_a) and self.is_sym_var_resolved(sym_b):
            # Both symbolic variables are resolved so check if their results are equal.
            val_a = self.get_sym_var_value(sym_a)
            val_b = self.get_sym_var_value(sym_b)
            if val_a != val_b:
                print(
                    "ERROR: values for {} and {} are different: {} and {}".format(
                        sym_a, sym_b, val_a, val_b
                    )
                )
            self.symvars_union_find.union(sym_a, sym_b)
        else:
            # Neither variable is resolved so it really doesn't matter the order
            # in which we union.
            self.symvars_union_find.union(sym_a, sym_b)

    def is_var_resolved(self, var: Union[Variable, Constant], func):
        symvar = self.get_sym_var(var, func)
        return self.is_sym_var_resolved(symvar)

    def is_sym_var_resolved(self, symvar: SymVar):
        rep = self.symvars_union_find.find(symvar)
        return rep in self._symvar_data

    def link_args_and_returns(self, callsite, caller_function, new_function):
        if isinstance(callsite, OverlayCall):
            # Link up the arguments.
            for var in callsite.arguments:
                if str(var) in callsite.arg_as_map:
                    for as_var in callsite.arg_as_map[str(var)]:
                        self.set_equal(as_var, caller_function, var, new_function)
                else:
                    self.set_equal(var, caller_function, var, new_function)

            # Link up return values.
            for var in callsite.returns:
                if str(var) in callsite.ret_as_map:
                    for as_var in callsite.ret_as_map[str(var)]:
                        self.set_equal(var, caller_function, as_var, new_function)
                else:
                    self.set_equal(var, caller_function, var, new_function)
        elif isinstance(callsite, (InternalCall, HighLevelCall)):
            # In the InternalCall case, things are a bit more complicated
            # because we want to link the argument and return variables which
            # are often represented by physically different variables in the IR.
            assert len(callsite.arguments) == len(callsite.function.parameters_ssa)
            for i in range(len(callsite.arguments)):
                if isinstance(callsite.arguments[i], Constant):
                    # We may have to add constants to a new_function
                    if callsite.arguments[i] not in new_function.var_to_symvar_local:
                        symvar = new_function.analyzer.symbolize_var(
                            callsite.arguments[i], new_function
                        )
                        new_function.set_sym_var_local(callsite.arguments[i], symvar)
                self.set_equal(
                    callsite.arguments[i],
                    caller_function,
                    # callsite.function.parameters_ssa[i],
                    callsite.arguments[i],
                    new_function,
                )

            if len(callsite.function.return_values_ssa) == 1:
                self.set_equal(
                    callsite.lvalue,
                    caller_function,
                    callsite.function.return_values_ssa[0],
                    new_function,
                )
        else:
            print("ERROR: Unhandled callsite type in link_args_and_returns")
            sys.exit(-1)

    def link_state_variables(self, callsite, caller_function, new_function):
        # Link up the state variables into the appropriate slots.
        for var in self.state_variables:
            mapping = caller_function.call_node_state_var_mappings[callsite][var]
            assert len(mapping) == 2
            entry_param, exit_param = mapping[0], mapping[1]

            # Link the entry value to the the entry slot of the next function
            caller_entry = caller_function.callsite_entry_state_vars[callsite][var]
            callee_entry = new_function.entry_state_vars[var]
            caller_exit = caller_function.callsite_exit_state_vars[callsite][var]
            callee_exit = new_function.exit_state_vars[var]
            self.set_equal(caller_entry, caller_function, callee_entry, new_function)
            self.set_equal(caller_exit, caller_function, callee_exit, new_function)

    def add_new_down_call_function(self, callsite, caller_function):
        dest = None
        if isinstance(callsite, OverlayCall):
            if callsite.loop_continue:
                dest = self.overlay_graph.find_overlay_function_by_name(callsite.dest.name)
            else:
                dest = callsite.dest
        elif isinstance(callsite, InternalCall):
            dest = self.overlay_graph.find_overlay_function(callsite.function)
        elif isinstance(callsite, HighLevelCall):
            dest = self.overlay_graph.find_overlay_function(callsite.function)

        new_function = AnalysisFunction(dest, self)
        self.live_functions.append(new_function)
        caller_function.callees[callsite] = new_function
        new_function.callers.append(caller_function)
        self.partial_call_all(new_function)
        return new_function

    def down_call(self, caller_function: AnalysisFunction, callsite: OverlayCall):
        new_function = self.add_new_down_call_function(callsite, caller_function)

        if self.strategy.command_fixpoint:
            return

        self.link_args_and_returns(callsite, caller_function, new_function)
        self.link_state_variables(callsite, caller_function, new_function)

    def prepend(
        self,
        ancestor: Union[OverlayFunction, InternalCall],
        callsite: Union[InternalCall, OverlayCall],
    ):
        """
        Prepends a function to this graph. This is a utility function that is
        used by the up call function and is the equivalent of up calling to
        only one possible call site. Another way of viewing this is that we are
        attaching ourselves as a subtree to this function at this callsite.
        """
        # Get "our" version of the function since by name since this may be a
        # deep copy.
        our_function = self.add_function(ancestor.name)

        # Get "our version of the callsite from our version of the function because
        # this may be a deep copy.
        our_callsite = None
        for x in get_all_call_sites_in_function(our_function.under):
            # A hacky way for a shallow comparison. Compare only the first line.
            # TODO: fix later
            if str(x).splitlines()[0] == str(callsite).splitlines()[0]:
                our_callsite = x
                break
        if our_callsite is None:
            print("ERROR: cannot find callsite")
            sys.exit(-1)

        # Add the correct caller and callee relationship.
        our_function.callees[our_callsite] = self.root
        self.root.callers.append(our_function)

        self.link_args_and_returns(our_callsite, our_function, self.root)
        self.link_state_variables(our_callsite, our_function, self.root)

        # Set the new root to be the prepended function.
        self.root = our_function

        # If the callsite is an OverlayCall, then set the condition to True
        if isinstance(callsite, OverlayCall) and not self.strategy.command_fixpoint:
            self.set_var_value(callsite.cond, our_function, True)

    def up_call_choose(self, func, callsite):
        self.prepend(func, callsite)

    def up_call(self) -> List:
        """
        Up call has move semantics so the analyzer that was upcalled will return
        n new analyzers and the original analyzer should never be used again. Up
        calling also implies that the root should be up called since it doesn't
        semantically make sense for a node that is not the root to be upcalled
        because it will already have a concretely defined ancestor.
        """
        new_analyzers = []

        # Find the call sites where you could possibly be called from:
        up_call_sites = self.find_up_call_sites(self.root)

        for func, site in up_call_sites:
            # Clone ourselves
            analyzer = copy.deepcopy(self)

            # Increment their ids
            analyzer.id = next(analyzer_counter)

            # Prepend to the current graph
            analyzer.prepend(func, site)

            try:
                analyzer.run_to_fixpoint()
            except InconsistentStateError as error:
                print("ERROR: InconsistentStateError -- " + str(error))
                print("Found at callsite: \n{}:\n{}".format(site, func.name))

                answer = input("Would you like to prune [yes/no]: ")
                if answer == "yes":
                    continue

            new_analyzers.append(analyzer)

        return new_analyzers

    def find_up_call_sites(
        self, root: AnalysisFunction
    ) -> List[Tuple[OverlayFunction, Union[OverlayCall, InternalCall]]]:
        """
        Finds the call sites where you could have been called from.
        """
        xrefs = []
        call_sites = get_all_call_sites(self.overlay_graph)
        for func, site in call_sites:
            if isinstance(site, OverlayCall):
                if site.dest == root.under:
                    xrefs.append((func, site))
            elif isinstance(site, (InternalCall, HighLevelCall)):
                if site.function == root.under.func:
                    xrefs.append((func, site))
            else:
                print("ERROR: invalid call site type: {}".format(type(site)))
                sys.exit(-1)
        return xrefs

    def traverse_nodes(self) -> List[Tuple[Any, AnalysisFunction]]:
        nodes = []
        for (node, func_id) in self._var_to_symvar.keys():
            for func in self.live_functions:
                if func.id == func_id:
                    nodes.append((node, func))
        return nodes

    def get_digraph(self) -> Digraph:
        self.counter = count()
        # Initialize the graph and graph attributes

        # TODO: change the fact that they are all in the same cluster but this
        #   is okay for a small example because it looks better
        g = Digraph(name="c")
        # g = Digraph(name='cluster_{}'.format(next(self.counter)))
        g.attr("node", shape="record")
        g.graph_attr.update({"rankdir": "LR", "newrank": "true"})

        # Maps AnalysisFunction objects to digraph handles.
        digraph_function_handles = {}

        # Go through and create all the function bodies but don't link up any
        # of the CALL nodes.
        for func in self.live_functions:
            handle, subgraph = func.get_digraph(self.counter)
            digraph_function_handles[func] = handle
            g.subgraph(subgraph)

        # Go through again and link up the CALL nodes to the correct functions.
        for func in self.live_functions:
            for stmt in func.under.statements:
                if isinstance(stmt, OverlayCall):
                    call_node_handle = func.call_node_digraph_handles[stmt]
                    if stmt in func.callees and func.callees[stmt] in digraph_function_handles:
                        function_handle = digraph_function_handles[func.callees[stmt]]
                        g.edge(call_node_handle, function_handle)
                        continue
                    stub_label = "{}_stub".format(stmt.dest.name)
                    stub_handle = "{}_stub_{}".format(stmt.dest.name, id(func))
                    g.node(stub_handle, label=stub_label)
                    g.edge("{}:target".format(call_node_handle), stub_handle)
                for ir in stmt.ir:
                    if isinstance(ir, InternalCall):
                        call_node_handle = func.call_node_digraph_handles[ir]
                        if ir in func.callees and func.callees[ir] in digraph_function_handles:
                            function_handle = digraph_function_handles[func.callees[ir]]
                            g.edge(call_node_handle, function_handle)

        # Draw the symvar equalities, making sure not to double draw any
        # undirected edges.
        do_not_add = set()
        for symvar, neighbors in self.drawn_equalities.items():
            for neighbor in neighbors:
                if (symvar, neighbor) not in do_not_add:
                    g.edge(str(symvar), str(neighbor), color="red", dir="none")
                    do_not_add.add((neighbor, symvar))

        return g

    def view_digraph(self):
        g = self.get_digraph()
        # print(g.source)
        g.view()

    def run_to_fixpoint(self):
        changed = True
        while changed:
            changed = False

            # First resolve all nodes that can be resolved without dependencies.
            changed |= self.strategy.resolve_ir_vars()

            # Check whether or not the strategy yields now information from any
            # IR instruction.
            for func in self.live_functions:
                for stmt in func.under.statements:
                    changed |= self.strategy.update_node(stmt, func)
                    for ir in stmt.ir:
                        changed |= self.strategy.update_ir(ir, func)

    def prepare_pickle(self):
        """
        Prepares the Analyzer to be pickled. No operations should be called on
        the analyzer until the corresponding unpickle function is called.
        """
        return

    def finish_unpickle(self):
        """
        Prepares the Analyzer after it has been freshly unpickled. No operations
        should be called on the Analyzer after pickling until this function is
        run.
        """
        return

    def get_function_id_list(self) -> str:
        ret = ""
        for function in self.live_functions:
            ret += "{}: {}\n".format(function.id, function.under.name)
        return ret

    def get_symvar_from_ir_name(self, ir_var_name):
        for var, symvar in self._var_to_symvar.items():
            if str(var[0]) == ir_var_name:
                return symvar
        return None

    def deduce_path_from_root(self, var, func):
        # Want to do a traversal up to the root and mark any conditionals as
        # true along the way.
        current = func
        while current != self.root:
            assert len(current.callers) == 1
            parent = current.callers[0]

            # Find the callsite in the parent and if its conditional then mark
            # it as true.
            callsite = next((k for (k, v) in parent.callees.items() if v == current), None)
            if callsite is None:
                print("Error, could not find callsite for function")
                sys.exit(-1)
            if isinstance(callsite, OverlayCall):
                self.set_var_value(
                    callsite.cond,
                    parent,
                    bool(not callsite.cond_complement),
                    deduce=False,
                )

            current = parent
