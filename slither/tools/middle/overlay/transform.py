import logging
import sys
from collections import deque, defaultdict
from itertools import count
from typing import List, Tuple, Dict, Any

from slither import Slither

from slither.tools.middle.overlay.ast.graph import OverlayGraph
from slither.tools.middle.overlay.ast.function import overlay_function_from_basic_block
from slither.tools.middle.overlay.util import OverlayCall, NodeType, OverlayFunction, OverlayNode, is_return, is_end_if, add_edge, remove_edge, copy, Condition, OverlayITE, add_node_after, get_ssa_variables_read, get_ssa_variables_defined, get_ssa_variables_used, Phi, Binary, Length, add_node_before, rewrite_ir_variable_by_name, rewrite_variable_in_all_successors, Assignment, is_loop_call, is_end_loop, OperationWithLValue, TemporaryVariableSSA, ReferenceVariableSSA, remove_all_edges

logger = logging.getLogger("transform")
# logger.setLevel(logging.DEBUG)

# Counter needed to name new SSA vars. This is necessary to avoid violating SSA
# when duplicating nodes for our CFG transformation.
dup_ssa_var_counter = count()


def main():
    if len(sys.argv) != 2:
        print("Usage: python transform.py contract.sol")
        sys.exit(-1)
    slither = Slither(sys.argv[1])
    graph = OverlayGraph(slither)
    outline_all_conditionals(graph)
    compress_all_phi_nodes(graph)
    print(graph.to_text_repr())
    graph.view_digraph()


def convert_all_calls(graph: OverlayGraph):
    """
    Convert all calls from internal calls to overlay calls. This allows us to
    keep better track of things like global variable writes among others.
    """
    for function in graph.functions:
        for stmt in function.statements.copy():
            if stmt.node.internal_calls:
                # Create the callee
                assert len(stmt.node.internal_calls) == 1
                callee = graph.find_overlay_function(stmt.node.internal_calls[0])
                assert callee is not None
                c = OverlayCall(callee)
                c.ir = stmt.ir

                bb = [stmt]
                yank_and_replace_basic_block(graph, bb, c)
                resolve_ssa_data_dependencies(graph, list(c.dest.statements), c, function, c.dest)


def outline_all_conditionals(graph: OverlayGraph):
    """Outlines each basic block in a conditional into its own function"""
    for function in graph.functions.copy():
        # Must iterate through the nodes in reverse topological ordering for this to work.
        # TODO: this is pretty fragile so I might want to change this later into two passes
        #       the main idea is that the LOOP needs to have all IF transformations done
        #       internally before doing the IFLOOP transformation. Otherwise, the IFLOOP
        #       transformation gets confused. Reverse BFS order works for now.
        order = list(reversed(graph.get_bfs_ordering(function).copy()))
        for statement in order:
            if statement.type == NodeType.IF:
                logger.debug("Outlining IF..")
                outline_conditional_if(graph, function, statement)
                # graph.save_digraph()
            if statement.type == NodeType.IFLOOP:
                logger.debug("Outlining LOOP..")
                outline_conditional_loop(graph, function, statement)
                # graph.save_digraph()


def outline_conditional_if(graph: OverlayGraph, function: OverlayFunction, statement: OverlayNode):
    assert statement.type == NodeType.IF
    assert len(statement.node.sons) == 2

    # Outline the loop bodies into their own functions.
    true_block, false_block = statement.node.sons[0], statement.node.sons[1]
    for succ in statement.succ.copy():
        # If there is an ENDIF directly after the IF that means that the ELSE
        # branch is missing so we don't have to inline it.
        if succ.type == NodeType.ENDIF:
            continue

        # Try to gather the basic block starting from the successor but stop if
        # we encounter an ENDIF or ENDLOOP.
        bb = gather_basic_block(succ)

        # Get the condition of the if statement. Slither doesn't tell us which
        # branch corresponds to true or false so we need to do some guessing.
        # For now, I am going to guess that the first son is true and the second
        # son is false.
        cond = list(filter(lambda x: isinstance(x, Condition), statement.ir))[0]

        f, c = outline_new_function(graph, function, bb, cond.value)

        if succ.node == false_block:
            c.cond_complement = True

    # Find the END_IF to go with this if by DFS but make sure not to go through
    # any END_LOOP barriers. We need to take this precaution because otherwise
    # trying to find our matching END_IF would become ambiguous. The only time
    # this rule can be broken is if there is a matching if_loop that we have
    # already seen
    dq = deque(statement.succ)
    visited = set()
    loop_enter_counter = 0
    current = None
    while len(dq) > 0:
        current = dq.pop()

        if current.type == NodeType.ENDIF:
            break

        if current.type == NodeType.IFLOOP or current.type == NodeType.STARTLOOP:
            loop_enter_counter += 1

        if current.type == NodeType.ENDLOOP and loop_enter_counter <= 0:
            continue
        loop_enter_counter -= 1

        if current in visited:
            continue

        visited.update(current.succ)
        dq.extend(current.succ)

    end_statement = current

    # Flatten the CFG only looking at the branches that are "viable" meaning
    # that they do not start with an END_IF.
    attachment_point = statement
    last_succ = None
    viable_branches = list(filter(lambda x: x.type != NodeType.ENDIF, statement.succ.copy()))

    for branch in viable_branches:
        # If the new function contains a return then we don't have to do this
        branch_contains_return = False
        for stmt in branch.dest.statements:
            if is_return(stmt):
                branch_contains_return = True
        if branch_contains_return:
            continue

        # Sever the body nodes.
        branch.prev.remove(statement)
        list(branch.succ)[0].prev.remove(branch)
        statement.succ.remove(branch)
        branch.succ = set()

        # Attach at the attachment_point.
        branch.prev.add(attachment_point)
        attachment_point.succ.add(branch)

        # Set up for the next iteration.
        attachment_point = branch
        last_succ = branch

    # If the end statement is not an ENDIF that means this is some weird control
    # flow with returns. So we don't need to attach the endif.
    if not is_end_if(end_statement) or last_succ is None:
        return

    # Add the last connection as a special case.
    add_edge(last_succ, end_statement)

    # In order to handle more nefarious control flow, we also need to detach
    # the ENDIF node from everything that is not the last_succ.
    must_detach = list(filter(lambda x: x != last_succ, end_statement.prev))
    for prev_node in must_detach:
        remove_edge(prev_node, end_statement)


def outline_new_function(
    graph: OverlayGraph, function: OverlayFunction, bb: List[OverlayNode], cond=None
) -> Tuple[OverlayFunction, OverlayCall]:
    # Create the new function and call site.
    f = overlay_function_from_basic_block(bb, function.contract)
    c = OverlayCall(f, cond)

    # Yank the provided basic block out of its context.
    yank_and_replace_basic_block(graph, bb, c)

    # Insert the newly created function into the graph.
    graph.functions.append(f)

    # Resolve all of the data dependencies that arise in function outlining.
    resolve_ssa_data_dependencies(graph, bb, c, function, f)

    # Add an initial ENTRY_POINT node to the newly created function.
    initial = OverlayNode(NodeType.ENTRYPOINT)
    initial.succ.add(bb[0])
    bb[0].prev.add(initial)
    f.statements.add(initial)

    # Return handles to the new function and the new call site.
    return f, c


def outline_conditional_loop(graph: OverlayGraph, function: OverlayFunction, stmt: OverlayNode):
    assert stmt.type == NodeType.IFLOOP

    # Try to detect whether this is a do-while structure or just a normal loop
    # structure. If it is a DO WHILE loop then the body of the loop will come
    # before the condition so stmt -> stmt.succ will be a backedge in a BFS
    # traversal.
    is_do_while = False
    ordering = graph.get_bfs_ordering(function)
    for succ in stmt.succ:
        if ordering.index(stmt) > ordering.index(succ):
            is_do_while = True

    # Some initial bookkeeping to get handles to relevant nodes.
    body_first = list(filter(lambda x: x.type != NodeType.ENDLOOP, stmt.succ))[0]
    cond = list(filter(lambda x: isinstance(x, Condition), stmt.ir))[0]

    # Gather the body of the loop.
    bb_body = gather_basic_block(body_first)

    # Outline the new function
    f, c = outline_new_function(graph, function, bb_body, cond.value)
    c.loop_call = True

    # The difference between the following two branches is that in the DO_WHILE
    # case, the IF will already be in the new function. In the WHILE case the IF
    # will still be in the old function. This type of asymmetry is needed because
    # in the DO_WHILE case we actually don't want to check the condition before
    # making the loop call but in the WHILE case we want to check the condition
    # first.
    cont_call = None
    if not is_do_while:
        # Coalesce the CALL and the IF.
        logger.debug("WHILE")
        try:
            coalesce_nodes(stmt, c)
        except AssertionError:
            print("Encountered an assertion error")
            # graph.save_digraph()
            sys.exit(-1)

        # Duplicate the call and the if into the end of the body of the new function.
        last = list(filter(lambda x: len(x.succ) == 0, f.statements))[0]
        anchor, as_map = duplicate_basic_block_after([stmt], last, f)
        duplicated_call, _ = duplicate_basic_block_after([c], anchor, f)
        duplicated_call.loop_continue = True

        # arg_as_map needs to be a default dictionary
        duplicated_call.arg_as_map = defaultdict(list)
        for k, v in as_map.items():
            duplicated_call.arg_as_map[k].append(v)

        cont_call = duplicated_call

    else:
        # Turn the back edge from the IF into a call. Normally the IF will be at
        # the end of the body and loop back into the top of the body (DO WHILE).
        # We need to copy the call from the body and turn this back edge into a
        # recursive call instead.
        logger.debug("DO WHILE")

        # Remove the back edge from the IF.
        assert len(stmt.succ) == 1
        succ = list(stmt.succ)[0]
        succ.prev.remove(stmt)
        stmt.succ.remove(succ)

        # Add the recursive call conditioned by the IF.
        rec_call = OverlayCall(c.dest, cond)
        rec_call.loop_continue = True

        stmt.succ.add(rec_call)
        rec_call.prev.add(stmt)
        f.statements.add(rec_call)

        cont_call = rec_call

    # Resolve again the SSA data dependencies because things might have changed.
    # We need to resolve against both the continue call and loop call.
    bb_body = gather_basic_block(body_first)
    resolve_ssa_data_dependencies(graph, bb_body, cont_call, f, f)

    # This is to allow arguments from the loop condition to flow into the first
    # iteration of the loop.
    resolve_ssa_data_dependencies(graph, bb_body, c, f, function, arguments_only=True)

    # The continue call needs all of the returns from the loop call as well so
    # that values changed in the last iteration of the loop can flow back.
    returns = [copy.copy(x) for x in cont_call.returns | c.returns]
    for x in returns:
        saved = copy.copy(x)

        # Rename to include the "cont" suffix so there is no name clash.
        x.name = x.name + "_cont"

        # We need to add an ITE just in case the continue call isn't called.
        # Otherwise, we wouldn't have a value to return in the case where the
        # loop continue call isn't taken.
        y = copy.copy(x)
        y.name = y.name + "_ret"
        node = OverlayITE(y, cont_call.cond, x, saved)
        add_node_after(f, cont_call, node)

        # # Add the variable to the ret_as_map of the cont call.
        cont_call.ret_as_map[str(x)].append(y)
        cont_call.returns.add(x)

        # Finally, add the variable to the ret_as_map of the loop call.
        c.ret_as_map[str(saved)].append(y)


def resolve_ssa_data_dependencies(
    graph: OverlayGraph,
    bb: List[OverlayNode],
    c: OverlayCall,
    original: OverlayFunction,
    f: OverlayFunction,
    arguments_only=False,
):
    """
    Resolve argument and return dependencies for the new function. The
    basic block might have had some data reads and writes that made its
    way outside the basic block. In order to ensure this is still valid IR
    we need to resolve all of these dependencies. In order to do this we
    need a full function analysis.
    """
    # TODO: I think I need to have something that looks for another call and
    #  "inherits" and imports or exports that don't already belong to current.

    bb_ssa_read = set()
    bb_ssa_written = set()

    # The new function imports anything that we have read but not written. We
    # also must make sure that the rest of the function also uses these values.
    for node in bb:
        var_read = get_ssa_variables_read(node, phi_read=False)
        var_defined = get_ssa_variables_defined(node)

        bb_ssa_read.update(var_read)
        bb_ssa_written.update(var_defined)

    rest_of_function_used = set()
    for stmt in original.statements:
        # TODO: deal with global variables
        var_used = get_ssa_variables_used(stmt)
        rest_of_function_used.update(var_used)
    c.arguments = bb_ssa_read.difference(bb_ssa_written).intersection(rest_of_function_used)

    if arguments_only:
        return

    # The new function exports anything written that that rest of the function
    # also reads.
    rest_of_function_read = set()
    for stmt in original.statements:
        # TODO: deal with global variables
        if stmt.node is not None:
            rest_of_function_read.update(get_ssa_variables_read(stmt))

    if c.loop_continue:
        # There are no return values for a loop continue call.
        c.returns = set()
    else:
        c.returns = bb_ssa_written.intersection(rest_of_function_read)


def gather_basic_block(start: OverlayNode, ends: List[NodeType] = None) -> List[OverlayNode]:
    """
    Gathers all the overlay nodes that compose a basic block starting at the
    specified node. A basic block ends when a node has any of the following
    properties:
        1. We have already visited it.
        2. It has more than one parent (prev).
        3. It's type is one of the specified types in the end parameter.
        4. It's type is an ENDLOOP without a previous BEGIN.
        5. It's type is an ENDIF without a previous BEGINIF
    """
    bb = [start]
    visited = {start}
    current = start
    loop_begin_count = 0
    if_begin_count = 1 if start.type == NodeType.IF else 0
    while len(current.succ) == 1 and len(list(current.succ)[0].prev) == 1:
        n = list(current.succ)[0]

        # Check if this is a funky control flow. We might encounter and ENDLOOP
        # if there is a break statement. However, we should be able to absorb a
        # transformed LOOP (straight line code) into our bb even when it is
        # delimited by IFLOOP and ENDLOOP. Thus, we cannot stop indiscriminately
        # at ENDLOOP.
        if n.type == NodeType.IFLOOP or n.type == NodeType.STARTLOOP:
            loop_begin_count += 1
        if n.type == NodeType.IF:
            if_begin_count += 1

        if n.type == NodeType.ENDLOOP:
            if loop_begin_count > 0:
                loop_begin_count -= 1
            else:
                break
        if n.type == NodeType.ENDIF:
            if if_begin_count > 0:
                if_begin_count -= 1
            else:
                break

        # Check that it is not in ends
        if ends is not None and n.type in ends:
            break
        # Check that it is not visited
        if n in visited:
            break

        bb.append(n)
        current = n

    return bb


def yank_and_replace_basic_block(graph: OverlayGraph, bb: List[OverlayNode], replace: OverlayNode):
    """Yanks the basic block in question out of its context and replaces it."""
    assert len(bb) >= 1

    # Get a list of all the incoming edges and outgoing edges from the bb. Be
    # careful to only count the edges that do not point internally.
    incoming = set()
    outgoing = set()
    reference = set(bb)
    for node in bb:
        for succ in node.succ.copy():
            if succ not in reference:
                outgoing.add(succ)
                succ.prev.add(replace)
                succ.prev.remove(node)
                node.succ.remove(succ)
        for prev in node.prev.copy():
            if prev not in reference:
                incoming.add(prev)
                prev.succ.add(replace)
                prev.succ.remove(node)
                node.prev.remove(prev)
    replace.succ = outgoing
    replace.prev = incoming

    # TODO: change this to something more efficient later
    # Inefficiently remove the block from its function and add the replacement.
    for function in graph.functions:
        if function.statements >= set(bb):
            function.statements = function.statements.difference(set(bb))
            function.statements.add(replace)


def coalesce_nodes(a: OverlayNode, b: OverlayNode):
    """
    Coalesces node b into node a. That is b is flattened below node a in the
    CFG. This function also verifies that b does not have any neighbors outside
    of node a; because in that case, coalescing looses its meaning.
    """
    assert b.prev == {a} or b.prev == {}
    assert b.succ == {a} or b.succ == {}
    assert b in a.succ

    remove_all_edges(b)

    # Let b inherit a's successors
    for succ in a.succ:
        if succ != b:
            add_edge(b, succ)

    # a's successors only consist of b now.
    for succ in a.succ.copy():
        remove_edge(a, succ)
    add_edge(a, b)


def duplicate_basic_block_after(
    bb: List[OverlayNode], anchor: OverlayNode, function: OverlayFunction
) -> Tuple[OverlayNode, Dict[str, Any]]:
    """
    Inline a basic block out of context after the anchor node. Returns the new
    last node attached along with a dictionary that maps any nodes we have
    replaced.
    """
    assert len(bb) >= 1

    # Make a copy of all the nodes in the basic block.
    bb = [copy.copy(x) for x in bb]

    # Maps the old ssa names to the duplicated ones
    old_to_dup_ssa = {}

    # Do some renaming to avoid violating SSA while duplicating.
    for node in bb:
        new_ir = []
        for ir in node.ir:
            if isinstance(ir, OperationWithLValue):
                ir = copy.deepcopy(ir)
                lvalue = copy.copy(ir.lvalue)

                # I don't think I need to deal with temporary variables right
                # now I don't think there will be any overlap with those. So
                # only perform this operation if we are not dealing with temp
                # variables.
                if not isinstance(lvalue, TemporaryVariableSSA) and not isinstance(
                    lvalue, ReferenceVariableSSA
                ):
                    old_name = lvalue.name
                    new_name = "{}_dup".format(old_name)
                    old_to_dup_ssa[str(ir.lvalue)] = lvalue

                    lvalue.name = new_name
                    ir.lvalue = lvalue

            new_ir.append(ir)
        node.ir = new_ir

    # Go through and for each value, if it is in the dictionary, then replace
    # it with its new duplicated value. Note, this is not responsible for
    # replacement outside (after) this basic block. That is left up to the
    # programmer.
    for node in bb:
        for ir in node.ir:

            if isinstance(ir, Phi):
                ir.rvalues = [old_to_dup_ssa[x] if x in old_to_dup_ssa else x for x in ir.rvalues]

            elif isinstance(ir, Binary):
                ir.variable_left = (
                    old_to_dup_ssa[str(ir.variable_left)]
                    if str(ir.variable_left) in old_to_dup_ssa
                    else ir.variable_left
                )
                ir.variable_right = (
                    old_to_dup_ssa[str(ir.variable_left)]
                    if str(ir.variable_right) in old_to_dup_ssa
                    else ir.variable_right
                )

            elif isinstance(ir, (Condition, Length)):
                continue

            else:
                print(
                    "ERROR: Unhandled ir type trying to duplicate basic block: {}".format(type(ir))
                )
                sys.exit(-1)

    first, last = bb[0], bb[-1]
    first.prev.add(anchor)
    last.succ.update(anchor.succ.copy())
    anchor.succ.add(first)

    function.statements.update(set(bb))

    return last, old_to_dup_ssa


################################################################################
# Post Transformation Processing
################################################################################


def compress_all_phi_nodes(graph: OverlayGraph):
    for function in graph.functions:
        changed = True
        while changed:
            changed = False
            changed |= try_compress_phi_node(graph, function)


def try_compress_phi_node(graph: OverlayGraph, function: OverlayFunction) -> bool:
    """
    Compress the phi nodes in the function. This procedure requires a full
    function analysis and relies on the following intuition: assume that we have
    a loop counter `i` that is used to increment a loop. In SlithIR SSA, a for-
    loop initialization block might have a statement like the following:

    i_2 = phi(i_1, i_3)

    Here, i_2 is the value that is used in the loop and i_3 is the incremented
    value and i_1 is the initial value. This represents the idea that the `i`
    that is used in the loop could either be the initial `i` or the incremented
    `i`. However, once we transform the function we get the following form:

    i_2 = phi(i_1, i_3)
    i_3 = LOOP CALL(i_2)
    END LOOP

    In this case, the loop call will take care of the entire loop and thus, i_2
    can never be i_3 so the phi node is extraneous. We can reduce to:

    i_2 = i_1
    i_3 = LOOP CALL(i_2)
    END LOOP

    But now we encounter another problem because if i_2 is used after the loop,
    it will always be the initial value, which is not correct. In reality, we
    want uses of i_2 after the loop to have the value phi(i_1, i_3). We can add
    a phi node after the loop call that reflects this. Renaming is necessary to
    avoid name clashes in SSA. We will also need to iterate through the rest of
    the function and rename all uses of i_2 to our new value. Finally we get:

    i_2 = i_1
    i_3 = LOOP CALL(i_2)
    i_dup_2 = phi(i_2, i_3)
    END LOOP
    # all uses of i_2 need to be renamed to i_dup_2
    """
    # Keeps track of the variables that get used as we traverse the ir.
    used = set()

    # Maps potential rvalues to the lvalue that they could push to.
    could_be = {}

    nodes = function.get_topological_ordering()
    for node_num, stmt in enumerate(nodes.copy()):
        for i, ir in enumerate(stmt.ir.copy()):
            if stmt.node.type == NodeType.ENDIF:
                resolved = [x for x in ir.rvalues if str(x) in used]

                # The statement is in an ENDIF so we need to loop backwards
                # until we find an IF
                true_false_mapping = [None, None]
                cond = None
                curr_node = nodes[node_num]
                while curr_node.type != NodeType.IF:
                    if isinstance(curr_node, OverlayCall):
                        cond = curr_node.cond
                        intersection = [x for x in ir.rvalues if x in curr_node.returns]
                        # assert len(intersection) <= 1
                        if intersection:
                            if curr_node.cond_complement:
                                true_false_mapping[1] = intersection[0]
                            else:
                                true_false_mapping[0] = intersection[0]
                    if curr_node.prev:
                        curr_node = list(curr_node.prev)[0]
                    else:
                        break

                if len(resolved) == 2 and isinstance(ir, Phi):
                    # This can be a special case in an if statement where the
                    # new value is actually a phi that is unaffected by the
                    # outlining.
                    true_branch, false_branch = None, None
                    if true_false_mapping[0]:
                        true_branch = true_false_mapping[0]
                        false_branch = next((x for x in resolved if x != true_branch))
                    elif true_false_mapping[1]:
                        false_branch = true_false_mapping[1]
                        true_branch = next((x for x in resolved if x != false_branch))
                    else:
                        print("ERROR: incomprehensible double resolution!")
                        sys.exit(-1)
                    new_node = OverlayITE(ir.lvalue, cond, true_branch, false_branch)
                    add_node_before(function, stmt, new_node)
                    stmt.ir.remove(ir)
                    continue

                assert len(resolved) == 1

                new_lvalue = copy.copy(ir.lvalue)
                new_lvalue.name = "{}_dup".format(ir.lvalue.name)
                if true_false_mapping[0] is not None and true_false_mapping[1] is not None:
                    # There is an if-else construct
                    new_node = OverlayITE(
                        new_lvalue, cond, true_false_mapping[0], true_false_mapping[1]
                    )
                    add_node_before(function, stmt, new_node)
                    rewrite_variable_in_all_successors(nodes[node_num], str(ir.lvalue), new_lvalue)
                elif true_false_mapping[0] is not None:
                    # It is an else-less construct
                    new_node = OverlayITE(new_lvalue, cond, true_false_mapping[0], ir.lvalue)
                    add_node_before(function, stmt, new_node)
                else:
                    print("ERROR: Invalid for loop construction!")
                    sys.exit(-1)

                stmt.ir.remove(ir)
                rewrite_variable_in_all_successors(nodes[node_num], str(ir.lvalue), new_lvalue)

                continue

            if stmt.node.type == NodeType.IFLOOP:
                if not isinstance(ir, Phi):
                    continue

                # The node is a Phi node so we try to compress it.
                resolved = [x for x in ir.rvalues if str(x) in used]
                assert len(resolved) == 1

                # Change the Phi node into an assignment since only one of
                # its arms are resolved.
                rvalue = resolved[0]
                new_node = Assignment(ir.lvalue, rvalue, rvalue)
                stmt.ir[i] = new_node

                # Add the branches of the phi that are not resolved to the
                # could_be map.
                unresolved = [x for x in ir.rvalues if str(x) not in used]
                for rvalue in unresolved:
                    could_be[rvalue] = ir.lvalue

                # Find the nearest loop call and look at the returns to
                # figure out what needs to be inserted as a ITE (phi) node.
                loop_call_idx = None
                old_lvalue_to_new_lvalue = {}
                for idx in range(node_num, len(nodes)):
                    if is_loop_call(nodes[idx]):
                        loop_call = nodes[idx]
                        for ret in loop_call.returns:
                            if ret in could_be:
                                old_lvalue = could_be[ret]
                                new_lvalue = copy.copy(could_be[ret])
                                new_lvalue.name = "{}_dup".format(old_lvalue.name)
                                old_lvalue_to_new_lvalue[old_lvalue] = new_lvalue
                                add_node_after(
                                    function,
                                    loop_call,
                                    OverlayITE(new_lvalue, loop_call.cond, ret, old_lvalue),
                                )
                        loop_call_idx = idx
                        break

                if loop_call_idx is None:
                    # This can happen if there is a loop continue call.
                    return True

                # Find the end loop associated with the loop call.
                end_loop_idx = None
                for idx in range(loop_call_idx, len(nodes)):
                    if is_end_loop(nodes[idx]):
                        end_loop_idx = idx
                        break

                if end_loop_idx is None:
                    print("ERROR: could not find matching end_loop")
                    sys.exit(-1)

                # For every node after the end loop, rename any variables
                # that we have introduced ITEs for.
                for idx in range(end_loop_idx, len(nodes)):
                    for _ir in nodes[idx].ir:
                        for old_lvalue, new_lvalue in old_lvalue_to_new_lvalue.items():
                            rewrite_ir_variable_by_name(_ir, str(old_lvalue), new_lvalue)

                return True

                # if len(resolved) > 1:
                #     # TODO: maybe later we can prune the branches of a PHI node
                #     #       even if we cannot fully resolve to an assignment.
                #     print("ERROR: more than one branch evaluated in Phi Node")
                #     exit(-1)

        used.update(
            [
                str(x)
                for x in get_ssa_variables_used(stmt, phi_read=True, all_vars=True)
                | get_ssa_variables_defined(stmt)
            ]
        )

    return False


if __name__ == "__main__":
    main()
