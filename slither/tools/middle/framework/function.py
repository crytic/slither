import html
import sys
import re
from collections import defaultdict
from itertools import count
from typing import Tuple, Dict, List, Set, Union

from slither.core.cfg.node import NodeType
from slither.slithir.operations import (
    Binary,
    Condition,
    InternalCall,
    Assignment,
    Phi,
    Return,
    HighLevelCall,
    SolidityCall,
)
from slither.slithir.variables import (
    LocalIRVariable,
    TemporaryVariableSSA,
    Constant,
    StateIRVariable,
    ReferenceVariableSSA,
)

# Must be a global variable to allow restoration upon pickling.
from slither.solc_parsing.variables.state_variable import StateVariableSolc
from slither.tools.middle.framework.tokens import (
    Variable,
    Value,
    CallSite,
    LeftBrace,
    RightBrace,
    NewLine,
    Annotation,
    Indent,
)
from slither.tools.middle.imports.graphivz import Digraph
from slither.tools.middle.overlay.ast.call import OverlayCall
from slither.tools.middle.overlay.ast.function import OverlayFunction
from slither.tools.middle.overlay.ast.ite import OverlayITE
from slither.tools.middle.overlay.ast.node import OverlayNode
from slither.tools.middle.overlay.util import (
    get_ssa_variables_read,
    get_ssa_variables_used,
    get_ssa_variables_defined,
    get_ssa_variables_used_in_ir,
    get_indent_list,
    get_all_call_sites_in_function,
)

counter = count()


class AnalysisFunction:
    id: int
    under: OverlayFunction
    callers: List

    # Maps the call nodes in this function to their AnalysisFunction callees.
    callees: Dict

    # Maps the call nodes to their digraph handles so they can be found in the
    # graph.
    call_node_digraph_handles: Dict

    # Maps a number to each instruction.
    number_to_instruction: Dict

    # Maps scoped vars to symbolic variables. This is to that we can tell the
    # difference between some symvars that are derived from duplicated nodes.
    # In general, this only creates and aesthetic improvement and does not
    # actually provide any new information.
    var_to_symvar_local: Dict

    # Holds a map from state_var to the most recent write and next read. This
    # tells you what to pass in to the call.
    call_node_state_var_mappings: dict

    state_var_counter = count(100)

    def __init__(self, under: OverlayFunction, analyzer):
        self.under = under
        self.callers = []
        self.callees = {}
        self.call_node_digraph_handles = {}
        self.number_to_instruction = {}
        self.analyzer = analyzer
        self.var_to_symvar_local = {}
        self.id = next(counter)
        self.sym_state_arguments = {}
        self.call_node_state_var_mappings = defaultdict(dict)

        # Each analysis function keeps a unique IR state variable to represent
        # the value of a certain state variable upon entry and exit to the
        # function.
        self.entry_state_vars: Dict[StateVariableSolc, StateIRVariable] = {}
        self.exit_state_vars: Dict[StateVariableSolc, StateIRVariable] = {}
        for state_var in self.analyzer.state_variables:
            entry_var = StateIRVariable(state_var)
            exit_var = StateIRVariable(state_var)
            self.entry_state_vars[state_var] = entry_var
            self.exit_state_vars[state_var] = exit_var
            entry_var.index = next(self.state_var_counter)
            exit_var.index = next(self.state_var_counter)
            self.symbolize_variable(entry_var)
            self.symbolize_variable(exit_var)

        # Also, keep track of this entry and exit state for each callsite
        self.callsite_entry_state_vars = {}
        self.callsite_exit_state_vars = {}
        for callsite in get_all_call_sites_in_function(self.under):
            self.callsite_entry_state_vars[callsite] = {}
            self.callsite_exit_state_vars[callsite] = {}
            for state_var in self.analyzer.state_variables:
                entry_var = StateIRVariable(state_var)
                exit_var = StateIRVariable(state_var)
                entry_var.index = next(self.state_var_counter)
                exit_var.index = next(self.state_var_counter)
                self.callsite_entry_state_vars[callsite][state_var] = entry_var
                self.callsite_exit_state_vars[callsite][state_var] = exit_var
                self.symbolize_variable(entry_var)
                self.symbolize_variable(exit_var)

        # Symbolize all the variables that are used in the function body.
        for stmt in self.under.statements:
            for var in get_ssa_variables_used(stmt, all_vars=True) | get_ssa_variables_defined(
                stmt
            ):
                self.symbolize_variable(var)

        self.resolve_state_vars_entry_and_exit()

        self.resolve_state_vars_for_calls()

    def symbolize_variable(self, var):
        symvar = self.analyzer.symbolize_var(var, self)
        self.set_sym_var_local(var, symvar)

    def resolve_state_vars_entry_and_exit(self):
        """
        Go through and hook up modifications of state variables to their
        corresponding SymStateArgs. Here, the SymStateArgs act kind of like
        slots. The incoming branch is hooked up to the first use of the state
        variable as an rvalue. The outgoing branch is hooked up to the last
        modification of the state variable. If there are no rvalue or lvalue
        uses then just connect the SymStateArgs to themselves.
        """

        def update_with_var_list(
            first_use: bool, last_write: bool, state_var, var_list: List
        ) -> (bool, bool):
            """
            Helper function that returns the updated first_use and last_write.
            Given a specific state variable to look for, a variable list, and
            a flag telling whether or not to consider the lvalue.
            """
            for var in var_list:
                if not isinstance(var, StateIRVariable):
                    continue
                if var.non_ssa_version != state_var:
                    continue
                first_use = var if first_use is None else first_use
                last_write = var
            return first_use, last_write

        for var in self.analyzer.state_variables:
            first_use = None
            last_write = None
            for stmt in self.under.get_topological_ordering():
                if stmt.type == NodeType.ENTRYPOINT:
                    continue
                if isinstance(stmt, OverlayCall):
                    if stmt not in self.callees:
                        continue
                    dest_analysis = self.callees[stmt]
                    first_use = (
                        dest_analysis.callsite_entry_state_vars[var]
                        if first_use is None
                        else first_use
                    )
                    last_write = dest_analysis.callsite_exit_state_vars[var]

                (first_use, last_write) = update_with_var_list(
                    first_use, last_write, var, get_ssa_variables_read(stmt, phi_read=False)
                )
                (first_use, last_write) = update_with_var_list(
                    first_use, last_write, var, get_ssa_variables_defined(stmt, phi_read=False)
                )
                for ir in stmt.ir:
                    if isinstance(ir, InternalCall):
                        first_use = (
                            self.callsite_entry_state_vars[ir][var]
                            if first_use is None
                            else first_use
                        )
                        last_write = self.callsite_exit_state_vars[ir][var]

            if first_use is None and last_write is None:
                self.analyzer.set_equal(
                    self.entry_state_vars[var], self, self.exit_state_vars[var], self
                )
            elif first_use is not None and last_write is None:
                self.analyzer.set_equal(self.entry_state_vars[var], self, first_use, self)
                self.analyzer.set_equal(first_use, self, self.exit_state_vars[var], self)
            elif first_use is None and last_write is not None:
                self.analyzer.set_equal(last_write, self, self.exit_state_vars[var], self)
            else:
                self.analyzer.set_equal(self.entry_state_vars[var], self, first_use, self)
                self.analyzer.set_equal(self.exit_state_vars[var], self, last_write, self)

    def resolve_state_vars_for_calls(self):
        # TODO: resolve the state variables for each of the calls. Find the most
        #       recent write and the next read and hook them up
        def resolve_for_call(c: Union[OverlayCall, InternalCall], stmts: List[OverlayNode]):
            if isinstance(c, (InternalCall, HighLevelCall)):
                c_stmt = next((x for x in stmts if c in x.ir), None)
                c_idx = stmts.index(c_stmt)
            else:
                c_idx = stmts.index(c)

            total_variables_defined = set()
            for stmt in stmts:
                total_variables_defined.update(get_ssa_variables_defined(stmt))

            # Find the most recent write and the next read
            for var in self.analyzer.state_variables:
                most_recent_write = None
                next_read = None
                for i in reversed(range(0, c_idx)):
                    most_recent_write = next(
                        (
                            x
                            for x in get_ssa_variables_defined(stmts[i])
                            if isinstance(x, StateIRVariable) and x.non_ssa_version == var
                        ),
                        None,
                    )
                    if most_recent_write is not None:
                        break

                for i in range(c_idx + 1, len(stmts)):
                    next_read = next(
                        (
                            x
                            for x in get_ssa_variables_read(stmts[i], phi_read=False)
                            if isinstance(x, StateIRVariable) and x.non_ssa_version == var
                        ),
                        None,
                    )
                    if next_read is not None:
                        break
                self.call_node_state_var_mappings[c][var] = (most_recent_write, next_read)

                entry_var = self.callsite_entry_state_vars[c][var]
                exit_var = self.callsite_exit_state_vars[c][var]
                if most_recent_write is not None:
                    self.analyzer.set_equal(most_recent_write, self, entry_var, self)
                if next_read is not None:
                    self.analyzer.set_equal(next_read, self, exit_var, self)

            # Remove explicit state variables from the argument lists
            if isinstance(c, OverlayCall):
                c.arguments = set([x for x in c.arguments if not isinstance(x, StateIRVariable)])
                c.returns = set([x for x in c.returns if not isinstance(x, StateIRVariable)])

        stmts = self.under.get_topological_ordering()
        for stmt in stmts:
            if isinstance(stmt, OverlayCall):
                resolve_for_call(stmt, stmts)
            else:
                for ir in stmt.ir:
                    if isinstance(ir, (InternalCall, HighLevelCall)):
                        resolve_for_call(ir, stmts)

        for callsite in get_all_call_sites_in_function(self.under):
            for var in self.analyzer.state_variables:
                most_recent_write, next_read = self.call_node_state_var_mappings[callsite][var]
                if most_recent_write is not None:
                    entry_var = self.callsite_entry_state_vars[callsite][var]
                    self.analyzer.set_equal(entry_var, self, most_recent_write, self)
                if next_read is not None:
                    exit_var = self.callsite_exit_state_vars[callsite][var]
                    self.analyzer.set_equal(exit_var, self, next_read, self)

    def set_sym_var_local(self, var, symvar):
        if str(var) in self.var_to_symvar_local:
            return
        self.var_to_symvar_local[str(var)] = symvar

    def get_sym_var(self, var):
        # Check the local cache first, because the mappings might be more
        # accurate than the global mapping. If nothing is found then return the
        # result of the global lookup.
        if var in self.var_to_symvar_local:
            return self.var_to_symvar_local[var]
        return self.analyzer.get_sym_var(var, self)

    def get_all_vars(self) -> Set:
        ret = set()
        for stmt in self.under.statements:
            if isinstance(stmt, OverlayCall):
                ret.add(stmt.cond)
                for arg in stmt.arguments:
                    if arg in stmt.arg_as_map:
                        ret.update(stmt.arg_as_map[arg])
                    else:
                        ret.add(arg)
                for ret_var in stmt.returns:
                    if ret_var in stmt.ret_as_map:
                        ret.update(stmt.ret_as_map[ret_var])
                    else:
                        ret.add(ret_var)
            if isinstance(stmt, OverlayITE):
                ret.add(stmt.lvalue)
                ret.add(stmt.condition)
                ret.add(stmt.consequence)
                ret.add(stmt.alternative)
            for op in stmt.ir:
                ret.update(op.used)
        return ret

    def lookup_var_by_name(self, name):
        variables = self.get_all_vars()
        ret = next((x for x in variables if str(x) == name), None)
        return ret

    def print_human_readable_ir(self):
        print(self.get_human_readable_ir())

    def get_human_readable_ir(self, substitute=True, rec=False):
        """
        Prints a human readable representation of the current analysis function
        that includes the shape of the function and the values that have already
        been derived.
        """
        # Get the normal SSA IR representation with the calls annotated with
        # either the call or the function id of the callee.
        ret = ""
        for stmt in self.under.get_topological_ordering():
            if isinstance(stmt, OverlayCall):
                cid = find_key_in_dict(stmt, self.number_to_instruction)
                if substitute:
                    ret += "CID: {}\n".format(cid)
                ret += str(stmt).strip()
                ret += "\n"
            if isinstance(stmt, OverlayITE):
                ret += str(stmt).strip()
                ret += "\n"
            for ir in stmt.ir:
                if isinstance(ir, InternalCall):
                    cid = find_key_in_dict(stmt, self.number_to_instruction)
                    if substitute:
                        ret += "CID: {}\n".format(cid)
                ret += str(ir).strip()
                ret += "\n"
            ret += "\n"

        already_printed_resolved = set()
        for var in self.get_all_vars():
            name = None
            if isinstance(var, LocalIRVariable):
                name = var.ssa_name
            elif isinstance(var, TemporaryVariableSSA):
                name = var.name
            elif isinstance(var, Constant):
                # Constants don't really need to be resolved or annotated.
                continue
            elif isinstance(var, ReferenceVariableSSA):
                name = var.name
            elif isinstance(var, StateIRVariable):
                name = var.ssa_name
            else:
                print("ERROR: Unrecognized variable type for printing {}".format(type(var)))
                sys.exit(-1)

            if self.analyzer.is_var_resolved(var, self):
                value = self.analyzer.get_var_value(var, self)
                # If the variable is resolved then we want to substitute in the
                # value that it is resolved to.
                if name not in already_printed_resolved:
                    already_printed_resolved.add(name)

                    if substitute:
                        ret = re.sub(r"\b{}\b".format(name), "{{{} = {}}}".format(name, value), ret)
            else:
                # Otherwise, we want to annotate the free variables with their
                # id so that they can be more easily referenced.
                sym_id = self.analyzer.get_sym_var(var, self).id

                if sym_id in already_printed_resolved:
                    continue
                already_printed_resolved.add(sym_id)

                if substitute:
                    ret = re.sub(r"\b{}\b".format(name), "[{}: {}]".format(sym_id, name), ret)

        return ret

    def get_source_lines(self, func: OverlayFunction):
        # Get a topological ordering of the nodes in the function
        source_mapping_lines = set()
        filename = None
        for overlay_node in func.get_topological_ordering():
            if overlay_node.node is None:
                continue
            if overlay_node.node.type == NodeType.ENTRYPOINT:
                # For some reason, ENTRYPOINT nodes contain bunch of noisy
                # source mappings, so we will ignore them for now.
                continue
            if filename is None:
                filename = overlay_node.node.source_mapping["filename_absolute"]
            source_mapping_lines.update(overlay_node.node.source_mapping["lines"])

        return source_mapping_lines, filename

    def print_human_readable_source(self, rec=True, literal=False):
        """
        Tries to print the source level representation of the current function.
        This is a best effort endeavor as outlining will have inevitably
        obfuscated some of the parts of the logic. For example, what appears to
        be an overlay call in IR/SSA form might just be a conditional in the
        original source.
        """
        ret = ""

        source_mapping_lines, filename = self.get_source_lines(self.under)

        # If we are not sourcing recursively, we need to remove the lines that
        # are associated with our callees. Create a mapping from the line number
        # to the callee that occupies that line.
        potential_callees = set()
        for stmt in self.under.statements:
            if isinstance(stmt, OverlayCall):
                potential_callees.add(stmt.dest)
                continue
            for ir in stmt.ir:
                if isinstance(ir, InternalCall):
                    dest = self.analyzer.overlay_graph.find_overlay_function(ir.function)
                    potential_callees.add(dest)
        callee_mappings = {}
        if not rec:
            for callee in potential_callees:
                for line in self.get_source_lines(callee)[0]:
                    callee_mappings[line] = callee

        # Print the "hunk" that describes the current function. For now, we will
        # make the assumptions that the lines are generally contiguous and in
        # the same file.
        # TODO: a more precise writing out of hunks
        min_line, max_line = min(source_mapping_lines) - 1, max(source_mapping_lines)

        with open(filename, "r") as f:
            lines = f.readlines()

        # If literal reading is called for then just return the literal reading
        if literal:
            # Hacky fix to usually bad mapping information
            min_line = max(0, min_line - 1)
            return "\n".join(lines)

        ret += "=" * 80 + "\n"
        for i in range(min_line, max_line + 1):
            if i in callee_mappings:
                # Take the whitespace from the previous line.
                ret += re.match(r"^\s*", lines[max(0, i - 1)]).group()
                ret += "// {}\n".format(callee_mappings[i].name)
            else:
                ret += "{}: {}".format(i, lines[i])
        ret += "=" * 80 + "\n"
        ret += "Lines {} - {} from file: {}".format(min_line, max_line, filename)

        var_mapping = defaultdict(list)
        if self.under.func is None:
            used = set()
            for stmt in self.under.statements:
                for ir in stmt.ir:
                    used.update(ir.used)
            # TODO: resolve the used sets of the callers as well to make this
            #      more intuitive.
            for source_var in used:
                l = list(self.var_to_symvar_local.values())
                l.extend(self.analyzer.state_var_to_symvar.values())
                for sym_var in l:
                    if source_var.name == sym_var.var.name:
                        var_mapping[source_var].append(sym_var)
        else:
            for source_var in self.under.func.variables:
                l = list(self.var_to_symvar_local.values())
                l.extend(self.analyzer.state_var_to_symvar.values())
                for sym_var in l:
                    if source_var.name == sym_var.var.name:
                        var_mapping[source_var].append(sym_var)

        already_printed_resolved = set()  # To prevent double printing values
        for ir_var, var_list in var_mapping.items():
            resolved_sym_var = next(
                (x for x in var_list if self.analyzer.is_sym_var_resolved(x)), None
            )
            if resolved_sym_var is not None:
                if isinstance(ir_var, Constant):
                    # We don't need to consider constants.
                    continue

                if resolved_sym_var.name in already_printed_resolved:
                    continue
                already_printed_resolved.add(resolved_sym_var.name)

                # Print the value of the variable.
                ret = re.sub(
                    r"\b{}\b".format(ir_var.name),
                    "{{{} = {}}}".format(
                        ir_var.name, self.analyzer.get_sym_var_value(resolved_sym_var)
                    ),
                    ret,
                )
            else:
                if ir_var.name in already_printed_resolved:
                    continue
                already_printed_resolved.add(ir_var.name)

                # Show all of the ids that correspond to a certain source variable.
                ir_var_label = ["{}".format(x.id) for x in var_list]
                ret = re.sub(
                    r"\b{}\b".format(ir_var.name),
                    "{{{} -> {}}}".format(ir_var.name, ir_var_label),
                    ret,
                )

        print(ret)
        return

    def view_state_digraph(self):
        """
        Shows a digraph of state nodes as well as their values
        """
        g = Digraph(name="c")
        g.attr("node", shape="record")
        g.graph_attr.update({"rankdir": "LR"})
        func_node_handle = "{}_{}".format(self.under.name, next(counter))
        g.node(func_node_handle, label=self.under.name, color="blue")

        # # Create all the state variables:
        # for var in get_ssa_variables_in_function(self.under):
        #     if isinstance(var, StateIRVariable):
        #         var_handle = '{}'.format(str(var))
        #         g.node(var_handle, label=(str(var)))

        live_symvars = set()

        for var in self.entry_state_vars.values():
            var_handle = "{}".format(str(self.get_sym_var(var)))
            live_symvars.add(self.get_sym_var(var))
            g.edge(var_handle, func_node_handle)
        for var in self.exit_state_vars.values():
            var_handle = "{}".format(str(self.get_sym_var(var)))
            live_symvars.add(self.get_sym_var(var))
            g.edge(func_node_handle, var_handle)

        for callsite in get_all_call_sites_in_function(self.under):
            call_node_handle = "{}".format(str(callsite))
            g.node(call_node_handle, label=(str(callsite)), color="red")
            for var in self.callsite_entry_state_vars[callsite].values():
                var_handle = "{}".format(str(self.get_sym_var(var)))
                live_symvars.add(self.get_sym_var(var))
                # g.node(var_handle, label='{}_entry'.format(str(var)))
                g.edge(var_handle, call_node_handle)
            for var in self.callsite_exit_state_vars[callsite].values():
                var_handle = "{}".format(str(self.get_sym_var(var)))
                live_symvars.add(self.get_sym_var(var))
                # g.node(var_handle, label='{}_exit'.format(str(var)))
                g.edge(call_node_handle, var_handle)

        # Replace resolved symvars with their value
        for symvar in live_symvars:
            if self.analyzer.is_sym_var_resolved(symvar):
                g.node(
                    str(symvar),
                    label="{} = {}".format(symvar.name(), self.analyzer.get_sym_var_value(symvar)),
                    style="filled",
                )
            else:
                g.node(str(symvar), label="{}".format(symvar.name()))

        print(g.source)
        g.view()

    def get_digraph(self, my_counter) -> Tuple[str, Digraph]:
        """
        Returns the digraph object and a handle to the root (function) node
        """
        self.number_to_instruction.clear()

        # Initialize the graph and graph attributes
        # TODO: change the fact that they are all in the same cluster but this
        #   is okay for a small example because it looks better
        g = Digraph(name="c")
        # g = Digraph(name='cluster_{}'.format(next(my_counter)))
        g.attr("node", shape="record")
        g.graph_attr.update({"rankdir": "LR"})

        # Adds the root (function) node
        func_node_handle = "{}_{}".format(self.under.name, next(my_counter))
        func_node_label = "<id> FID: {} | <title> FUNCTION: {}|<params> params|<statements> statements |<returns> returns".format(
            self.id, self.under.name
        )
        g.node(func_node_handle, label=func_node_label, color="blue")

        for stmt in self.under.statements:
            self.add_statement_to_digraph(g, stmt, func_node_handle, my_counter)

        return func_node_handle, g

    def add_statement_to_digraph(self, g: Digraph, stmt, root_handle, my_counter):
        if isinstance(stmt, OverlayCall):
            # Handle the case where we have outlined a function. We know that
            # there will be no IR in this call so we can just continue.
            label = None
            num = next(my_counter)
            # Add the number to the label so we can reference this call
            name = "CALL__{}".format(num)
            if stmt.cond_complement:
                label = "<id> CID: {} | <title> CALL | <cond> NOT cond | <target> target | <args> args | <returns> returns".format(
                    num
                )
            else:
                label = "<id> CID: {} | <title> CALL | <cond> cond | <target> target | <args> args | <returns> returns".format(
                    num
                )
            g.node(name, label=label)
            self.number_to_instruction[num] = stmt
            self.call_node_digraph_handles[stmt] = name
            g.edge("{}:statements".format(root_handle), "{}:title".format(name))
            g.edge("{}:cond".format(name), str(self.get_sym_var(stmt.cond)))
            for i in stmt.arguments:
                g.edge("{}:args".format(name), str(self.get_sym_var(i)))
            for e in stmt.returns:
                g.edge("{}:returns".format(name), str(self.get_sym_var(e)))
            return

        if isinstance(stmt, OverlayITE):
            # We know there will be no ir in the OverlayITE
            label = "<title> ITE | <cond> cond | <true> true | <false> false | <result> result"
            name = "ITE__{}".format(next(my_counter))
            g.node(name, label=label)
            g.edge("{}:statements".format(root_handle), "{}:title".format(name))
            g.edge("{}:cond".format(name), str(self.get_sym_var(stmt.condition)))
            g.edge("{}:true".format(name), str(self.get_sym_var(stmt.consequence)))
            g.edge("{}:false".format(name), str(self.get_sym_var(stmt.alternative)))
            g.edge("{}:result".format(name), str(self.get_sym_var(stmt.lvalue)))

        # Create all the statement nodes
        for ir in stmt.ir:
            if isinstance(ir, Binary):
                label = "<title> {} | <left> left | <right> right | <result> result".format(
                    html.escape(str(ir.type))
                )
                name = "{}__{}".format(str(ir.type), next(my_counter))
                g.node(name, label=label)
                g.edge("{}:statements".format(root_handle), "{}:title".format(name))
                g.edge("{}:left".format(name), str(self.get_sym_var(ir.variable_left)))
                g.edge("{}:right".format(name), str(self.get_sym_var(ir.variable_right)))
                g.edge("{}:result".format(name), str(self.get_sym_var(ir.lvalue)))
            elif isinstance(ir, Condition):
                label = "<title> CONDITION | <value> value"
                name = "CONDITION__{}".format(next(my_counter))
                g.node(name, label=label)
                g.edge("{}:statements".format(root_handle), "{}:title".format(name))
                g.edge("{}:value".format(name), str(self.get_sym_var(ir.value)))
            elif isinstance(ir, InternalCall):
                num = next(my_counter)
                # Add the number to the label so we can reference this call
                label = "<id> ID: {} | <title> CALL | <target> target | <args> args | <returns> returns".format(
                    num
                )
                name = "CALL__{}".format(num)
                g.node(name, label=label)
                self.number_to_instruction[num] = ir
                self.call_node_digraph_handles[ir] = name
                g.edge("{}:statements".format(root_handle), "{}:title".format(name))
                for a in ir.arguments:
                    g.edge("{}:args".format(name), str(self.get_sym_var(a)))
                g.edge("{}:returns".format(name), str(self.get_sym_var(ir.lvalue)))
            elif isinstance(ir, Assignment):
                label = "<title> ASSIGN | <left> left | <right> right"
                name = "ASSIGN__{}".format(next(my_counter))
                g.node(name, label=label)
                self.call_node_digraph_handles[stmt] = name
                g.edge("{}:statements".format(root_handle), "{}:title".format(name))
                g.edge("{}:left".format(name), str(self.get_sym_var(ir.lvalue)))
                g.edge("{}:right".format(name), str(self.get_sym_var(ir.rvalue)))
            elif isinstance(ir, Phi):
                label = "<title> PHI | <args> args | <result> result"
                name = "PHI__{}".format(next(my_counter))
                g.node(name, label=label)
                g.edge("{}:statements".format(root_handle), "{}:title".format(name))
                for arg in ir.rvalues:
                    g.edge("{}:args".format(name), str(self.get_sym_var(arg)))
                g.edge("{}:result".format(name), str(self.get_sym_var(ir.lvalue)))

        # Reflect all the values that are associated with the symbolic variables
        for symvar in self.var_to_symvar_local.values():
            if self.analyzer.is_sym_var_resolved(symvar):
                # For all the symvars that have values, use the value as the label
                g.node(
                    str(symvar),
                    label="ID: {} - {} = {}".format(
                        symvar.id, symvar.name(), self.analyzer.get_sym_var_value(symvar)
                    ),
                    style="filled",
                )
            else:
                # Otherwise, use the simplified printer
                g.node(str(symvar), label="ID: {} - {}".format(symvar.id, symvar.name()))

    def to_tokens(self, indentation_level: int):
        tokens = []

        for stmt in self.under.get_topological_ordering():

            if isinstance(stmt, OverlayCall):
                if (
                    self.analyzer.is_var_resolved(stmt.cond, self)
                    and self.analyzer.get_var_value(stmt.cond, self) == True
                    and stmt.cond_complement
                ):
                    continue
                if (
                    self.analyzer.get_var_value_or_default(stmt.cond, self, None) == False
                    and self.analyzer.strategy.hide_resolved
                ):
                    continue
                # If its a loop continue and its not resolved
                if stmt.loop_continue and not stmt in self.callees:
                    tokens.extend(
                        [Indent(stmt, self) for _ in range(indentation_level)]
                        + [CallSite(stmt, self), NewLine(stmt, self)]
                    )
                elif stmt in self.callees:
                    tokens.extend(
                        stmt.to_tokens(
                            self, body=self.callees[stmt].to_tokens(0), indent=indentation_level
                        )
                    )
                else:
                    tokens.extend(stmt.to_tokens(self, indent=indentation_level))

            elif isinstance(stmt, OverlayITE):
                lvalue_resolved = self.analyzer.is_var_resolved(stmt.lvalue, self)
                condition_resolved = self.analyzer.is_var_resolved(stmt.condition, self)
                consequence_resolved = self.analyzer.is_var_resolved(stmt.consequence, self)
                alternative_resolved = self.analyzer.is_var_resolved(stmt.alternative, self)
                if self.analyzer.strategy.hide_resolved:
                    if (
                        lvalue_resolved
                        and condition_resolved
                        and consequence_resolved
                        and alternative_resolved
                    ):
                        continue
                tokens.extend(stmt.to_tokens(self, indent=indentation_level))

            else:
                staging = stmt.to_tokens(self, indentation_level)
                for ir in stmt.ir:
                    if isinstance(ir, Phi):
                        continue
                    if isinstance(ir, (InternalCall, HighLevelCall)):
                        if ir in self.callees:
                            # Find the index of the call token associated with this ir and inline the function
                            call_idx = staging.index(CallSite(ir, self))
                            del staging[call_idx]
                            callee_tokens = self.callees[ir].to_tokens(indentation_level + 1)
                            staging[call_idx:call_idx] = (
                                [LeftBrace(ir, self), NewLine(ir, self)]
                                + callee_tokens
                                + get_indent_list(indentation_level, ir, self)
                                + [RightBrace(ir, self)]
                            )
                        else:
                            # Append the arguments to the callsite.
                            call_idx = staging.index(CallSite(ir, self))
                            arg_tokens = [LeftBrace(ir, self)]
                            for arg in ir.arguments:
                                arg_tokens.append(Variable(arg, ir, self))
                            arg_tokens.append(RightBrace(ir, self))
                            staging[call_idx + 1 : call_idx + 1] = arg_tokens
                    elif isinstance(ir, SolidityCall):
                        # Since Solidity calls cannot be inlined we just attach
                        # the arguments to the callsite
                        call_idx = staging.index(CallSite(ir, self))
                        arg_tokens = [LeftBrace(ir, self)]
                        for arg in ir.arguments:
                            arg_tokens.append(Variable(arg, ir, self))
                        arg_tokens.append(RightBrace(ir, self))
                        staging[call_idx + 1 : call_idx + 1] = arg_tokens
                    else:
                        if not isinstance(ir, Return) and all(
                            self.analyzer.is_var_resolved(var, self)
                            for var in get_ssa_variables_used_in_ir(ir)
                        ):
                            if self.analyzer.strategy.hide_resolved:
                                # Remove all the lines associated with this ir
                                staging = [x for x in staging if x.assoc_stmt != ir]
                tokens.extend(staging)

        for idx, token in enumerate(tokens.copy()):
            if isinstance(token, Variable):
                # Convert all the known variables into their value equivalents.
                try:
                    if self.analyzer.strategy.get_value_in_strategy:
                        val = self.analyzer.strategy.get_var_value(token.var, token.func)
                    else:
                        val = self.analyzer.get_var_value(token.var, token.func)
                    if not self.analyzer.strategy.hide_resolved:
                        # Add the value as an annotation.
                        tokens[idx].annotation = Annotation(val)
                    elif self.analyzer.is_var_resolved(token.var, token.func):
                        tokens[idx] = Value(val, token.var, token.assoc_stmt, token.func)
                except KeyError:
                    # Might not be in our function since things might be inlined.
                    pass

        return tokens

    def get_live_source_mappings(self):
        # mappings[filename][function] = lines
        mappings = defaultdict(lambda: defaultdict(set))
        for stmt in self.under.get_topological_ordering():
            if isinstance(stmt, OverlayCall):
                if stmt in self.callees:
                    inner_mappings = self.callees[stmt].get_live_source_mappings()
                    for k, v in inner_mappings.items():
                        # V is a dictionary of sets
                        for x, y in v.items():
                            mappings[k][x].update(y)
            elif isinstance(stmt, OverlayITE):
                pass
            elif isinstance(stmt, OverlayNode):
                if stmt.type == NodeType.ENTRYPOINT or stmt.type == NodeType.ENDIF:
                    continue
                for ir in stmt.ir:
                    if (isinstance(ir, (InternalCall, HighLevelCall))) and ir in self.callees:
                        # We have confirmed to go down this path
                        inner_mappings = self.callees[ir].get_live_source_mappings()
                        for k, v in inner_mappings.items():
                            for x, y in v.items():
                                mappings[k][x].update(y)
                filename = stmt.node.source_mapping["filename_absolute"]
                lines = stmt.node.source_mapping["lines"]
                mappings[filename][self].update(lines)
        return mappings

    def get_source_var_by_name(self, name):
        return next((x for x in self.under.func.variables if name == str(x)), None)

    def find_stmt_containing_source_mapping(self, filename, current):
        for stmt in self.under.get_topological_ordering():
            if isinstance(stmt, OverlayNode) and stmt.node is not None:
                if stmt.node.type == NodeType.ENDIF or stmt.node.type == NodeType.ENTRYPOINT:
                    continue
                if stmt.node.source_mapping["filename_absolute"] == filename:
                    start = stmt.node.source_mapping["start"]
                    end = stmt.node.source_mapping["start"] + stmt.node.source_mapping["length"]
                    if start <= current <= end:
                        return stmt
        return None


def find_key_in_dict(value, my_dict):  # TODO: replace all calls with dict.get(key)
    for k, v in my_dict.items():
        if v == value:
            return k
    return None
