import copy

from slither.tools.middle.framework.tokens import Indent
from slither.tools.middle.overlay.ast.call import OverlayCall
from slither.tools.middle.overlay.ast.function import OverlayFunction
from slither.tools.middle.overlay.ast.ite import OverlayITE
from slither.tools.middle.overlay.ast.node import OverlayNode
from slither.core.cfg.node import NodeType
from slither.slithir.operations import (
    Phi,
    OperationWithLValue,
    Return,
    Binary,
    Condition,
    Index,
    TypeConversion,
    Assignment,
    Length,
    InternalCall,
    HighLevelCall,
)
from slither.slithir.variables import (
    LocalIRVariable,
    StateIRVariable,
    TemporaryVariableSSA,
    Constant,
    ReferenceVariableSSA,
)


def is_loop_begin(node: OverlayNode) -> bool:
    if node.node is None:
        return False
    if node.node.type == NodeType.STARTLOOP:
        return True
    else:
        return False


def is_loop_call(node: OverlayNode) -> bool:
    if isinstance(node, OverlayCall):
        return node.loop_call
    return False


def is_overlay_call(node: OverlayNode) -> bool:
    return isinstance(node, OverlayCall)


def is_cont_call(node: OverlayNode) -> bool:
    if isinstance(node, OverlayCall):
        return node.loop_continue
    return False


def is_end_loop(node: OverlayNode) -> bool:
    return node.type == NodeType.ENDLOOP


def is_return(node: OverlayNode) -> bool:
    return node.type == NodeType.RETURN


def is_end_if(node: OverlayNode) -> bool:
    return node.type == NodeType.ENDIF


def rewrite_variable_in_all_successors(node, old_var_name, new_var):
    curr_node = node
    while len(curr_node.succ) > 0:
        assert len(curr_node.succ) == 1
        curr_node = list(curr_node.succ)[0]
        rewrite_node_variable_by_name(curr_node, old_var_name, new_var)


def rewrite_node_variable_by_name(node: OverlayNode, old_var_name, new_var):
    if isinstance(node, OverlayCall):
        # Rewrite the condition if we need to.
        if str(node.cond) == old_var_name:
            node.cond = new_var
        # Arguments can be rewritten into the "pass as" form.
        for arg in [x for x in node.arguments if str(x) == old_var_name]:
            node.arg_as_map[arg].append(new_var)
        # Returns can also be rewritten into the "pass as" form.
        for ret in [x for x in node.returns if str(x) == old_var_name]:
            node.ret_as_map[ret].append(new_var)
    for ir in node.ir:
        rewrite_ir_variable_by_name(ir, old_var_name, new_var)


def rewrite_ir_variable_by_name(ir, old_var_name, new_var):
    if isinstance(ir, Return):
        ir.values = [new_var if str(x) == old_var_name else x for x in ir.values]
    elif isinstance(ir, Binary):
        ir.variable_left = new_var if str(ir.variable_left) == old_var_name else ir.variable_left
        ir.variable_right = new_var if str(ir.variable_right) == old_var_name else ir.variable_right
    elif isinstance(ir, Condition):
        ir.value = new_var if str(ir.value) == old_var_name else ir.value
    elif isinstance(ir, Phi):
        ir.rvalues = [new_var if str(x) == old_var_name else x for x in ir.rvalues]
    elif isinstance(ir, Assignment):
        ir.rvalue = new_var if str(ir.rvalue) == old_var_name else ir.rvalue

    # TODO: I don't know what to do for these operation types
    elif isinstance(ir, Index):
        pass
    elif isinstance(ir, TypeConversion):
        pass
    elif isinstance(ir, Length):
        pass

    else:
        print("Unrecognized IR type for rewriting: {}".format(type(ir)))
        exit("-1")


def get_name(var) -> str:
    if isinstance(var, LocalIRVariable):
        return var.ssa_name
    elif isinstance(var, TemporaryVariableSSA):
        return var.name
    elif isinstance(var, Constant):
        # Constants don't really need to be resolved or annotated.
        return ""
    elif isinstance(var, ReferenceVariableSSA):
        return var.name
    elif isinstance(var, StateIRVariable):
        return var.name


def get_ssa_variables_used_in_ir(ir, phi_read=True):
    ret = set()
    if not phi_read and isinstance(ir, Phi):
        ret.add(ir.lvalue)
        return ret
    ret.update([x for x in ir.read])
    ret.update([x for x in ir.used if isinstance(x, (LocalIRVariable, StateIRVariable))])
    return ret


def get_ssa_variables_used(n: OverlayNode, phi_read=True, all_vars=False):
    """
    A special function that resolves much of the same purpose as the above
    function with the key difference being tha this function looks for the ssa
    variables that are used and not just read.
    """
    ret = set()
    if isinstance(n, OverlayCall):
        ret.add(n.cond)
        ret.update(n.arguments)
        ret.update(n.returns)
    elif isinstance(n, OverlayITE):
        ret.add(n.lvalue)
        ret.add(n.consequence)
        ret.add(n.alternative)
    elif n.node is not None:
        for ir in n.ir:
            if not phi_read and isinstance(ir, Phi):
                ret.add(ir.lvalue)
                continue
            if all_vars:
                ret.update([x for x in ir.read])
            else:
                ret.update(
                    [x for x in ir.used if isinstance(x, (LocalIRVariable, StateIRVariable))]
                )
    return ret


def get_ssa_variables_read(n: OverlayNode, phi_read=True, constants=False):
    """
    A special function to manually look through the ir read variables. This is
    because slither doesn't count a phi node as reading its arguments, which
    leads to an incorrect transformation so we have to special case this.

    It is important to note that the way SlithIR is set up right now, we do NOT
    want to count entry point phi nodes as having read its variables. In other
    words, we want to count every phi node except for the entry point phi nodes.
    """
    ret = set()
    # TODO: this needs more thought
    #  and n.type != NodeType.ENTRYPOINT
    if isinstance(n, OverlayCall):
        ret.add(n.cond)
    elif isinstance(n, OverlayITE):
        ret.add(n.consequence)
        ret.add(n.alternative)
    elif n.node is not None:
        for ir in n.ir:
            if not phi_read and isinstance(ir, Phi):
                continue
            if not constants:
                ret.update(
                    [x for x in ir.read if isinstance(x, (LocalIRVariable, StateIRVariable))]
                )
            else:
                ret.update([x for x in ir.read])
    return ret


def get_ssa_variables_defined(n: OverlayNode, phi_read=True):
    """
    A special function to manually look through SSA definitions
    """
    ret = set()
    if isinstance(n, OverlayCall):
        ret.add(n.cond)
        return ret
    if isinstance(n, OverlayITE):
        ret.add(n.lvalue)
        return ret
    if n.node is not None:
        for ir in n.ir:
            if not phi_read and isinstance(ir, Phi):
                continue
            if isinstance(ir, OperationWithLValue):
                ret.update([ir.lvalue])
    return ret


def get_ssa_variables_in_function(f: OverlayFunction):
    """
    A function to get all the variables defined in a function
    """
    vars = set()
    for stmt in f.get_topological_ordering():
        vars.update(get_ssa_variables_read(stmt))
        vars.update(get_ssa_variables_used(stmt))
        vars.update(get_ssa_variables_defined(stmt))
    return vars


def get_state_argument_variables_defined(n: OverlayNode):
    """
    Returns the implicit argument exports if applicable
    """
    if isinstance(n, OverlayCall):
        return n.dest
    elif n.node is not None:
        return n.node.state_variables_read + n.node.state_variables_written
    else:
        return set()


def remove_edge(a: OverlayNode, b: OverlayNode):
    """
    Removes an edge from a -> b if one exists
    """
    if b in a.succ and a in b.prev:
        a.succ.remove(b)
        b.prev.remove(a)


def add_edge(a: OverlayNode, b: OverlayNode):
    """
    Adds the edge a -> b
    """
    a.succ.add(b)
    b.prev.add(a)


def remove_all_edges_between(a: OverlayNode, b: OverlayNode):
    """
    Removes all possible connections between a and b.
    """
    a.succ.discard(b)
    a.prev.discard(b)
    b.succ.discard(a)
    b.prev.discard(a)


def remove_all_edges(n: OverlayNode):
    """
    Removes all incoming and outgoing edges from n
    """
    for prev in n.prev:
        prev.succ.remove(n)
    for succ in n.succ:
        succ.prev.remove(n)
    n.succ.clear()
    n.prev.clear()


def add_node_after(func: OverlayFunction, anchor: OverlayNode, node: OverlayNode):
    """
    Adds the node after the anchor in func. The anchor node must be in func.
    """
    remove_all_edges(node)

    node.succ = copy.copy(anchor.succ)
    node.prev = {anchor}

    for succ in anchor.succ:
        succ.prev.remove(anchor)
        succ.prev.add(node)
    anchor.succ = {node}

    func.statements.add(node)


def add_node_before(func: OverlayFunction, anchor: OverlayNode, node: OverlayNode):
    """
    Adds the node before the anchor in func. The anchor node must be in func.
    """
    remove_all_edges(node)

    node.succ = {anchor}
    node.prev = copy.copy(anchor.prev)

    for prev in anchor.prev:
        prev.succ.remove(anchor)
        prev.succ.add(node)
    anchor.prev = {node}

    func.statements.add(node)


def get_indent_list(level, stmt, func):
    return [Indent(stmt, func) for _ in range(level)]


def create_hashable(var, func):
    # Symvars are uniquely determined by a var node and an AnalysisFunction.
    return str(var), func.id


def get_all_call_sites(graph):
    call_sites = []
    for func in graph.functions:
        call_sites.extend([(func, x) for x in get_all_call_sites_in_function(func)])
    return call_sites


def get_all_call_sites_to(graph, f):
    call_sites = []
    for func, callsite in get_all_call_sites(graph):
        if isinstance(callsite, OverlayCall):
            dest = callsite.dest
        elif isinstance(callsite, InternalCall):
            dest = callsite.function
        elif isinstance(callsite, HighLevelCall):
            dest = callsite.function
        else:
            print("Error: unhandled callsite type: {}".format(type(callsite)))
            exit(-1)
        if dest == f:
            call_sites.append((func, callsite))
    return call_sites


def resolve_nearest_concrete_parent(graph, func):
    if func.func is not None:
        return func
    else:
        current = func.func
        while current is None:
            callsites = get_all_call_sites_to(graph, func)
            callsites = [
                (y, x)
                for (y, x) in callsites
                if not isinstance(x, OverlayCall)
                or isinstance(x, OverlayCall)
                and not x.loop_continue
            ]
            assert len(callsites) == 1
            current, _ = callsites[0]
        return current


def get_all_call_sites_in_function(func: OverlayFunction):
    """Returns an ordered list of callsites"""
    call_sites = []
    for node in func.get_topological_ordering():
        if isinstance(node, OverlayCall):
            call_sites.append(node)
        for ir in node.ir:
            if isinstance(ir, InternalCall) or isinstance(ir, HighLevelCall):
                call_sites.append(ir)
    return call_sites
