import logging
from functools import cmp_to_key
from typing import Set
from typing import Union

from slither.core.cfg.node import Node
from slither.core.declarations import (
    Function,
)
from slither.core.declarations.function import FunctionType
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.function_top_level import FunctionTopLevel
from slither.core.declarations.modifier import Modifier
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.exceptions import SlithIRError
from slither.slithir.operations import (
    Assignment,
    Binary,
    Condition,
    Delete,
    EventCall,
    HighLevelCall,
    Index,
    InitArray,
    InternalCall,
    InternalDynamicCall,
    Length,
    LibraryCall,
    LowLevelCall,
    Member,
    NewArray,
    NewContract,
    NewElementaryType,
    NewStructure,
    OperationWithLValue,
    Phi,
    PhiCallback,
    Return,
    Send,
    SolidityCall,
    Transfer,
    TypeConversion,
    Unary,
    Unpack,
    Nop,
)
from slither.slithir.operations.codesize import CodeSize
from slither.slithir.operations.operation import Operation
from slither.slithir.utils.ssa_version_tracker import VarStates, StateVarDefRecorder
from slither.slithir.variables import (
    Constant,
    LocalIRVariable,
    ReferenceVariable,
    StateIRVariable,
    TemporaryVariable,
    TupleVariable,
)
from slither.slithir.variables.variable import SlithIRVariable

logger = logging.getLogger("SSA_Conversion")

###################################################################################
###################################################################################
# region SlihtIR variables to SSA
###################################################################################
###################################################################################


def transform_slithir_vars_to_ssa(
    function: Union[FunctionContract, Modifier, FunctionTopLevel]
) -> None:
    """
    Transform slithIR vars to SSA (TemporaryVariable, ReferenceVariable, TupleVariable)
    """
    variables = []
    for node in function.nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, OperationWithLValue) and not ir.lvalue in variables:
                variables += [ir.lvalue]

    tmp_variables = [v for v in variables if isinstance(v, TemporaryVariable)]
    for idx, _ in enumerate(tmp_variables):
        tmp_variables[idx].index = idx
    ref_variables = [v for v in variables if isinstance(v, ReferenceVariable)]
    for idx, _ in enumerate(ref_variables):
        ref_variables[idx].index = idx
    tuple_variables = [v for v in variables if isinstance(v, TupleVariable)]
    for idx, _ in enumerate(tuple_variables):
        tuple_variables[idx].index = idx


###################################################################################
###################################################################################
# region SSA conversion
###################################################################################
###################################################################################

# pylint: disable=too-many-arguments,too-many-locals,too-many-nested-blocks,too-many-statements,too-many-branches
def _add_phi_rvalue(phi: Phi, rvalue):
    """Propagates refers to information for Phi lvalues
    Appends refers_to information from rvalue to lvalue, typically
    when adding to a Phi-node
    """
    phi.rvalues.append(rvalue)
    lvalue = phi.lvalue
    if isinstance(lvalue, (LocalIRVariable, TemporaryVariable)) and lvalue.is_storage:
        lvalue.refers_to.update(rvalue.refers_to)


def ir_to_ssa_form(ir: Operation, state: VarStates, rec: StateVarDefRecorder):
    """
    Produces SSA form IR from IR
    Args:
        ir (Operation)
        state (VarStates)
        rec (StateVarDefRecorder)
    NOTE: The order of operation is important, lvalues MUST be
    computed after r-values are computed. If not the r-value
    version might use the latest def. That would cause this IR
    var = var + 1
    to incorrectly become:
    var_1 = var_1 + 1
    instead of the correct:
    var_1 = var_0 + 1
    """

    def get_ssa(var):
        return state.get(var)

    def add_def(lval):
        return state.add(lval)

    def add_refers_to(op: OperationWithLValue):
        if not isinstance(op.lvalue, LocalIRVariable):
            return
        if not op.lvalue.is_storage:
            return

        # NOTE (hbrodin): Given how IR is currently generated assignments to storage is
        # only made through temporary variables, that is a storage type is not the lvalue
        # of a binary or unary operation or other generic OperationWithLValue.
        # If that ever changes this function needs to change.
        assert isinstance(op, Assignment)

        if isinstance(op.rvalue, ReferenceVariable):
            refers_to = op.rvalue.points_to_origin
            op.lvalue.add_refers_to(refers_to)
        elif not isinstance(op.rvalue, Constant):
            op.lvalue.add_refers_to(op.rvalue)

    def _get_traversal(values):
        ret = []
        for v in values:
            if isinstance(v, list):
                v = _get_traversal(v)
            else:
                v = state.get(v)
            ret.append(v)
        return ret

    def get_arguments(ir):
        return _get_traversal(ir.arguments)

    def get_rec_values(ir, f):
        # Use by InitArray and NewArray
        # Potential recursive array(s)
        ori_init_values = f(ir)

        return _get_traversal(ori_init_values)

    if isinstance(ir, Assignment):
        rvalue = get_ssa(ir.rvalue)
        lvalue = add_def(ir.lvalue)

        op = Assignment(lvalue, rvalue, ir.variable_return_type)
        add_refers_to(op)
        return op
    if isinstance(ir, Binary):
        variable_left = get_ssa(ir.variable_left)
        variable_right = get_ssa(ir.variable_right)
        lvalue = add_def(ir.lvalue)
        return Binary(lvalue, variable_left, variable_right, ir.type)
    if isinstance(ir, CodeSize):
        value = get_ssa(ir.value)
        lvalue = add_def(ir.lvalue)
        return CodeSize(value, lvalue)
    if isinstance(ir, Condition):
        return Condition(get_ssa(ir.value))
    if isinstance(ir, Delete):
        variable = get_ssa(ir.variable)
        lvalue = add_def(ir.lvalue)
        return Delete(lvalue, variable)
    if isinstance(ir, EventCall):
        name = ir.name
        return EventCall(name)
    if isinstance(ir, HighLevelCall):  # include LibraryCall
        destination = get_ssa(ir.destination)
        call_value = get_ssa(ir.call_value)
        call_gas = get_ssa(ir.call_gas)
        arguments = get_arguments(ir)

        if not isinstance(ir, LibraryCall):
            # This needs to happen before lvalue is computed otherwise
            # We might record the wrong def for a StateVariable
            rec.collect_before_call()

        lvalue = add_def(ir.lvalue)
        if isinstance(ir, LibraryCall):
            new_ir = LibraryCall(
                destination, ir.function_name, ir.nbr_arguments, lvalue, ir.type_call
            )
        else:
            new_ir = HighLevelCall(
                destination, ir.function_name, ir.nbr_arguments, lvalue, ir.type_call
            )
        new_ir.call_id = ir.call_id
        new_ir.call_value = call_value
        new_ir.call_gas = call_gas
        new_ir.arguments = arguments
        new_ir.function = ir.function
        return new_ir
    if isinstance(ir, Index):
        variable_left = get_ssa(ir.variable_left)
        variable_right = get_ssa(ir.variable_right)
        lvalue = add_def(ir.lvalue)
        return Index(lvalue, variable_left, variable_right, ir.index_type)
    if isinstance(ir, InitArray):
        init_values = get_rec_values(ir, lambda x: x.init_values)
        lvalue = add_def(ir.lvalue)
        return InitArray(init_values, lvalue)
    if isinstance(ir, InternalCall):
        args = get_arguments(ir)
        rec.collect_before_call()
        lvalue = add_def(ir.lvalue)
        new_ir = InternalCall(ir.function, ir.nbr_arguments, lvalue, ir.type_call)
        new_ir.arguments = args
        return new_ir
    if isinstance(ir, InternalDynamicCall):
        function = get_ssa(ir.function)
        arguments = get_arguments(ir)
        rec.collect_before_call()
        lvalue = add_def(ir.lvalue)
        new_ir = InternalDynamicCall(lvalue, function, ir.function_type)
        new_ir.arguments = arguments
        return new_ir
    if isinstance(ir, LowLevelCall):
        destination = get_ssa(ir.destination)
        call_value = get_ssa(ir.call_value)
        call_gas = get_ssa(ir.call_gas)
        arguments = get_arguments(ir)
        rec.collect_before_call()
        lvalue = add_def(ir.lvalue)
        new_ir = LowLevelCall(destination, ir.function_name, ir.nbr_arguments, lvalue, ir.type_call)
        new_ir.call_id = ir.call_id
        new_ir.call_value = call_value
        new_ir.call_gas = call_gas
        new_ir.arguments = arguments
        return new_ir
    if isinstance(ir, Member):
        variable_left = get_ssa(ir.variable_left)
        variable_right = get_ssa(ir.variable_right)
        lvalue = add_def(ir.lvalue)
        return Member(variable_left, variable_right, lvalue)
    if isinstance(ir, NewArray):
        arguments = get_rec_values(ir, lambda x: x.arguments)
        lvalue = add_def(ir.lvalue)
        new_ir = NewArray(ir.depth, ir.array_type, lvalue)
        new_ir.arguments = arguments
        return new_ir
    if isinstance(ir, NewElementaryType):
        arguments = get_arguments(ir)
        lvalue = add_def(ir.lvalue)
        new_ir = NewElementaryType(ir.type, lvalue)
        new_ir.arguments = arguments
        return new_ir
    if isinstance(ir, NewContract):
        arguments = get_arguments(ir)
        call_value = get_ssa(ir.call_value)
        call_salt = get_ssa(ir.call_salt)
        lvalue = add_def(ir.lvalue)
        new_ir = NewContract(ir.contract_name, lvalue)
        new_ir.arguments = arguments
        new_ir.call_value = call_value
        new_ir.call_salt = call_salt
        return new_ir
    if isinstance(ir, NewStructure):
        arguments = get_arguments(ir)
        lvalue = add_def(ir.lvalue)
        new_ir = NewStructure(ir.structure, lvalue)
        new_ir.arguments = arguments
        return new_ir
    if isinstance(ir, Nop):
        return Nop()
    if isinstance(ir, Return):
        values = get_rec_values(ir, lambda x: x.values)
        rec.collect_at_end()
        return Return(values)
    if isinstance(ir, Send):
        destination = get_ssa(ir.destination)
        call_value = get_ssa(ir.call_value)
        lvalue = add_def(ir.lvalue)
        return Send(destination, call_value, lvalue)
    if isinstance(ir, SolidityCall):
        arguments = get_arguments(ir)
        lvalue = add_def(ir.lvalue)
        new_ir = SolidityCall(ir.function, ir.nbr_arguments, lvalue, ir.type_call)
        new_ir.arguments = arguments
        return new_ir
    if isinstance(ir, Transfer):
        destination = get_ssa(ir.destination)
        call_value = get_ssa(ir.call_value)
        return Transfer(destination, call_value)
    if isinstance(ir, TypeConversion):
        variable = get_ssa(ir.variable)
        lvalue = add_def(ir.lvalue)
        return TypeConversion(lvalue, variable, ir.type)
    if isinstance(ir, Unary):
        rvalue = get_ssa(ir.rvalue)
        lvalue = add_def(ir.lvalue)
        return Unary(lvalue, rvalue, ir.type)
    if isinstance(ir, Unpack):
        tuple_var = get_ssa(ir.tuple)
        lvalue = add_def(ir.lvalue)
        return Unpack(lvalue, tuple_var, ir.index)
    if isinstance(ir, Length):
        value = get_ssa(ir.value)
        lvalue = add_def(ir.lvalue)
        return Length(value, lvalue)

    raise SlithIRError(f"Impossible ir copy on {ir} ({type(ir)})")


def insert_phi_after_call(node: Node, call_ir, var_state: VarStates):
    """Creates a phi function after calls to
    The phi-function will later be populated with identified writes to state variables
    """
    if not isinstance(call_ir, (InternalCall, HighLevelCall, InternalDynamicCall, LowLevelCall)):
        return
    if isinstance(call_ir, LibraryCall):
        return

    for variable in var_state.state_variables():
        if not is_used_later(node, variable):
            continue
        # The value after the call could be whatever it was before the call,
        # for other values it can hold (due to reentrancy or invoking state-
        # modifying functions) additional work is done after the full contract
        # is converted to SSA IR.
        old_def = var_state.get(variable)
        new_var = var_state.add(variable)
        phi_ir = PhiCallback(new_var, {node}, call_ir, old_def)
        node.add_ssa_ir(phi_ir)


def _record_store_through_ref(node: Node, op: OperationWithLValue, state: VarStates) -> None:
    """When a store through a ReferenceVariable is made simulate a write to the target by inserting a phi
    This ensures that StateVariables written via references get an additional version
    """
    # NOTE (hbrodin): Currently all lvalues of type ReferenceVariable seems to be
    # via assignment (not Binary, Unary etc.) if that changes need to change this function
    if isinstance(op, Assignment):
        if isinstance(op.lvalue, ReferenceVariable):
            origin = op.lvalue.points_to_origin
            if isinstance(origin, LocalIRVariable):
                if origin.is_storage:
                    for refers_to in origin.refers_to:
                        lvalue = state.add(refers_to.non_ssa_version)
                        phi = Phi(lvalue, set())
                        node.add_ssa_ir(phi)
                        _add_phi_rvalue(phi, origin)


def ir_nodes_to_ssa(node: Node, parent_state: VarStates, rec: StateVarDefRecorder):
    with parent_state.new_scope() as state:
        # NOTE (hbrodin): Dummy phi-nodes have been placed in a previous step.
        # This will ensure that the dummy phi-nodes are replace with correctly
        # #indexed phi-nodes according to current state when visiting block
        # having the phi-node.
        for i, n in enumerate(node.irs_ssa):
            if isinstance(n, Phi):
                # Replace the dummy phi with a correctly labeled phi
                lvalue = state.add(n.lvalue.non_ssa_version)
                new_ir = Phi(lvalue, n.nodes)
                for ir_var in n.rvalues:
                    _add_phi_rvalue(new_ir, ir_var)
                node.irs_ssa[i] = new_ir

        # Transform each IR operation into SSA form (except Phis which shouldn't be present)
        for ir in node.irs:
            assert not isinstance(ir, (Phi, PhiCallback))
            # if s is a non-phi statement (by design, no phi in non-ssa ir)
            ssa_irs = ir_to_ssa_form(ir, state, rec)
            ssa_irs.set_expression(ir.expression)
            ssa_irs.set_node(ir.node)
            node.add_ssa_ir(ssa_irs)

            # Additional care for calls, want to show that state variables might
            # have changed due to reentrancy or invoking another function that
            # changes storage vars.
            insert_phi_after_call(node, ssa_irs, state)
            _record_store_through_ref(node, ssa_irs, state)

        # Propagate relevant vars to successor phi operations
        for successor in node.sons:
            for n in successor.irs_ssa:
                if isinstance(n, Phi):
                    orig_var = n.lvalue.non_ssa_version
                    ssa_var = state.get(orig_var)
                    _add_phi_rvalue(n, ssa_var)

        # Order the successors to ensure that a successor (A) is visited after successor
        # (B) if dominance frontier of B is A. This is to ensure that refers_to
        # analysis gets correct information. It is not strictly needed for the correct
        # operation of assigning SSA values. The issue is that Phi-nodes have to be
        # Fully constructed (all rvalues assigned) before users of the def can propagate
        # refers_to information.
        # TODO (hbrodin): Is this correct? Does it cover all cases?
        def sortkey(x, y):
            return 1 if x in y.dominance_frontier else -1

        for successor in sorted(node.dominator_successors, key=cmp_to_key(sortkey)):
            ir_nodes_to_ssa(successor, state, rec)


def _add_param_return_ssa(function: Function, ssa_state: VarStates) -> None:
    def add(variables, addfunc):
        for var in filter(lambda x: x.name, variables):
            # Get the initial version and record it in the function
            ssa0 = ssa_state.get(var)

            addfunc(ssa0)

            if ssa0.is_storage:
                # Create a fake variable that represents the storage
                fake_var = ssa_state.add(var)
                fake_var.name = "STORAGE_" + fake_var.name
                fake_var.set_location("reference_to_storage")
                ssa0.refers_to = {fake_var}

    add(function.parameters, function.add_parameter_ssa)
    add(function.returns, function.add_return_ssa)


def add_ssa_ir(function: Function, ssa_state: VarStates = None):
    """
        Add SSA version of the IR
    Args:
        function
        all_state_variables_instances
    """

    # To allow for state variable constructors to be run
    abort = not function.is_implemented
    if function.function_type in (
        FunctionType.CONSTRUCTOR_VARIABLES,
        FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES,
    ):
        abort = False

    if abort:
        return

    if ssa_state is None:
        ssa_state = VarStates()

    # Create the initial version of all variables used (represents the default value)
    for var in function.variables:
        ssa_state.add(var)

    # Create a StateVarDefRecorder that is used to keep track of state variables at
    # different times or SSA IR generation (before any call, at end of functions)
    rec = StateVarDefRecorder(ssa_state, referenced_state_variables(function))

    # The state variable is used
    # For state variable constructor functions this will be a no-op because those
    # functions are run before initializing the ssa_state with all contract state
    # variables.
    for state_var in ssa_state.state_variables():
        if is_used_later(function.entry_point, state_var):
            # rvalues are fixed in solc_parsing.declaration.function
            function.entry_point.add_ssa_ir(Phi(ssa_state.get(state_var), set()))

    # Create initial version of named parameters/returns
    _add_param_return_ssa(function, ssa_state)

    # Adding phi-nodes based on control flow of function
    # This will place the initial phi-nodes at dominance frontiers of each node
    insert_placeholder_phis(function.nodes)

    # Transform IR to SSA ir by cloning IR nodes and add version info. This will also
    # append Phi-nodes after external calls (for any state variable currently used).
    ir_nodes_to_ssa(function.entry_point, ssa_state, rec)

    # Collect the final state of variables at the end of function
    # calls will have been made at points where a Return operation
    # was found as well.
    rec.collect_at_end()


# endregion
###################################################################################
###################################################################################
# region Helpers
###################################################################################
###################################################################################


def referenced_state_variables(function: Function) -> Set[StateVariable]:
    """Returns a set of all StateVariables that are referenced in a function"""
    variables = set()
    for node in function.nodes:
        variables.update(node.state_variables_written)
        variables.update(node.state_variables_read)
    return variables


def is_used_later(
    initial_node: Node,
    variable: Union[StateIRVariable, LocalVariable],
) -> bool:
    # TODO: does not handle the case where its read and written in the declaration node
    # It can be problematic if this happens in a loop/if structure
    # Ex:
    # for(;true;){
    #   if(true){
    #     uint a = a;
    #    }
    #     ..
    to_explore = {initial_node}
    explored = set()

    while to_explore:
        node = to_explore.pop()
        explored.add(node)
        if isinstance(variable, LocalVariable):
            if any(v.name == variable.name for v in node.local_variables_read):
                return True
            if any(v.name == variable.name for v in node.local_variables_written):
                return False
        if isinstance(variable, StateVariable):
            if any(
                v.name == variable.name and v.contract == variable.contract
                for v in node.state_variables_read
            ):
                return True
            if any(
                v.name == variable.name and v.contract == variable.contract
                for v in node.state_variables_written
            ):
                return False
        for son in node.sons:
            if not son in explored:
                to_explore.add(son)

    return False


# endregion
###################################################################################
###################################################################################
# region Phi Operations
###################################################################################
###################################################################################


def insert_placeholder_phis(nodes):
    """Insert Phi-nodes where needed"""

    def add_phi_for(node: Node, var: Union[LocalVariable, StateVariable]) -> bool:
        if isinstance(var, LocalVariable):
            lvalue = LocalIRVariable(var)
        elif isinstance(var, LocalIRVariable):
            lvalue = LocalIRVariable(var.non_ssa_version)
        elif isinstance(var, StateVariable):
            lvalue = StateIRVariable(var)
        else:
            assert isinstance(var, StateIRVariable)
            lvalue = StateIRVariable(var.non_ssa_version)
        node.add_ssa_ir(Phi(lvalue, set()))

    def have_phi_for(node, var: Union[LocalVariable, StateVariable]):
        if isinstance(var, SlithIRVariable):
            var = var.non_ssa_version
        for phi in filter(lambda x: isinstance(x, Phi), node.irs_ssa):
            if phi.lvalue.non_ssa_version == var:
                return True
        return False

    # Phase 1 place emtpy phi nodes (having dummy lvalue)
    workset = set()
    for node in filter(lambda n: n.dominance_frontier, nodes):
        for phi_node in node.dominance_frontier:
            for local_var in node.local_variables_written + node.state_variables_written:
                if not have_phi_for(phi_node, local_var):
                    add_phi_for(phi_node, local_var)
                    workset.add(phi_node)

    # Phase 2 - any phi-node is a 'def' and should thus be propagated. Iter until no change.
    while workset:
        node = workset.pop()
        for phi_node in node.dominance_frontier:
            for phi_ssa in node.irs_ssa:
                assert isinstance(phi_ssa, Phi)
                if not have_phi_for(phi_node, phi_ssa.lvalue):
                    add_phi_for(phi_node, phi_ssa.lvalue)
                    workset.add(phi_node)


# endregion
