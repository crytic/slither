import logging

from slither.core.cfg.node import NodeType
from slither.core.declarations import (
    Contract,
    Enum,
    Function,
    SolidityFunction,
    SolidityVariable,
    Structure,
)
from slither.core.declarations.solidity_import_placeholder import SolidityImportPlaceHolder
from slither.core.solidity_types.type import Type
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.top_level_variable import TopLevelVariable
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
    Push,
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
from slither.slithir.variables import (
    Constant,
    LocalIRVariable,
    ReferenceVariable,
    ReferenceVariableSSA,
    StateIRVariable,
    TemporaryVariable,
    TemporaryVariableSSA,
    TupleVariable,
    TupleVariableSSA,
)
from slither.slithir.exceptions import SlithIRError

logger = logging.getLogger("SSA_Conversion")

###################################################################################
###################################################################################
# region SlihtIR variables to SSA
###################################################################################
###################################################################################


def transform_slithir_vars_to_ssa(function):
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


def add_ssa_ir(function, all_state_variables_instances):
    """
        Add SSA version of the IR
    Args:
        function
        all_state_variables_instances
    """

    if not function.is_implemented:
        return

    init_definition = {}
    for v in function.parameters:
        if v.name:
            init_definition[v.name] = (v, function.entry_point)
            function.entry_point.add_ssa_ir(Phi(LocalIRVariable(v), set()))

    for v in function.returns:
        if v.name:
            init_definition[v.name] = (v, function.entry_point)

    # We only add phi function for state variable at entry node if
    # The state variable is used
    # And if the state variables is written in another function (otherwise its stay at index 0)
    for (_, variable_instance) in all_state_variables_instances.items():
        if is_used_later(function.entry_point, variable_instance):
            # rvalues are fixed in solc_parsing.declaration.function
            function.entry_point.add_ssa_ir(Phi(StateIRVariable(variable_instance), set()))

    add_phi_origins(function.entry_point, init_definition, {})

    for node in function.nodes:
        for (variable, nodes) in node.phi_origins_local_variables.values():
            if len(nodes) < 2:
                continue
            if not is_used_later(node, variable):
                continue
            node.add_ssa_ir(Phi(LocalIRVariable(variable), nodes))
        for (variable, nodes) in node.phi_origins_state_variables.values():
            if len(nodes) < 2:
                continue
            # if not is_used_later(node, variable.name, []):
            #    continue
            node.add_ssa_ir(Phi(StateIRVariable(variable), nodes))

    init_local_variables_instances = {}
    for v in function.parameters:
        if v.name:
            new_var = LocalIRVariable(v)
            function.add_parameter_ssa(new_var)
            if new_var.is_storage:
                fake_variable = LocalIRVariable(v)
                fake_variable.name = "STORAGE_" + fake_variable.name
                fake_variable.set_location("reference_to_storage")
                new_var.refers_to = {fake_variable}
                init_local_variables_instances[fake_variable.name] = fake_variable
            init_local_variables_instances[v.name] = new_var

    for v in function.returns:
        if v.name:
            new_var = LocalIRVariable(v)
            function.add_return_ssa(new_var)
            if new_var.is_storage:
                fake_variable = LocalIRVariable(v)
                fake_variable.name = "STORAGE_" + fake_variable.name
                fake_variable.set_location("reference_to_storage")
                new_var.refers_to = {fake_variable}
                init_local_variables_instances[fake_variable.name] = fake_variable
            init_local_variables_instances[v.name] = new_var

    all_init_local_variables_instances = dict(init_local_variables_instances)

    init_state_variables_instances = dict(all_state_variables_instances)

    initiate_all_local_variables_instances(
        function.nodes,
        init_local_variables_instances,
        all_init_local_variables_instances,
    )

    generate_ssa_irs(
        function.entry_point,
        dict(init_local_variables_instances),
        all_init_local_variables_instances,
        dict(init_state_variables_instances),
        all_state_variables_instances,
        init_local_variables_instances,
        [],
    )

    fix_phi_rvalues_and_storage_ref(
        function.entry_point,
        dict(init_local_variables_instances),
        all_init_local_variables_instances,
        dict(init_state_variables_instances),
        all_state_variables_instances,
        init_local_variables_instances,
    )


def generate_ssa_irs(
    node,
    local_variables_instances,
    all_local_variables_instances,
    state_variables_instances,
    all_state_variables_instances,
    init_local_variables_instances,
    visited,
):

    if node in visited:
        return

    if node.type in [NodeType.ENDIF, NodeType.ENDLOOP] and any(
        not father in visited for father in node.fathers
    ):
        return

    # visited is shared
    visited.append(node)

    for ir in node.irs_ssa:
        assert isinstance(ir, Phi)
        update_lvalue(
            ir,
            node,
            local_variables_instances,
            all_local_variables_instances,
            state_variables_instances,
            all_state_variables_instances,
        )

    # these variables are lived only during the liveness of the block
    # They dont need phi function
    temporary_variables_instances = {}
    reference_variables_instances = {}
    tuple_variables_instances = {}

    for ir in node.irs:
        new_ir = copy_ir(
            ir,
            local_variables_instances,
            state_variables_instances,
            temporary_variables_instances,
            reference_variables_instances,
            tuple_variables_instances,
            all_local_variables_instances,
        )

        new_ir.set_expression(ir.expression)
        new_ir.set_node(ir.node)

        update_lvalue(
            new_ir,
            node,
            local_variables_instances,
            all_local_variables_instances,
            state_variables_instances,
            all_state_variables_instances,
        )

        if new_ir:

            node.add_ssa_ir(new_ir)

            if isinstance(ir, (InternalCall, HighLevelCall, InternalDynamicCall, LowLevelCall)):
                if isinstance(ir, LibraryCall):
                    continue
                for variable in all_state_variables_instances.values():
                    if not is_used_later(node, variable):
                        continue
                    new_var = StateIRVariable(variable)
                    new_var.index = all_state_variables_instances[variable.canonical_name].index + 1
                    all_state_variables_instances[variable.canonical_name] = new_var
                    state_variables_instances[variable.canonical_name] = new_var
                    phi_ir = PhiCallback(new_var, {node}, new_ir, variable)
                    # rvalues are fixed in solc_parsing.declaration.function
                    node.add_ssa_ir(phi_ir)

            if isinstance(new_ir, (Assignment, Binary)):
                if isinstance(new_ir.lvalue, LocalIRVariable):
                    if new_ir.lvalue.is_storage:
                        if isinstance(new_ir.rvalue, ReferenceVariable):
                            refers_to = new_ir.rvalue.points_to_origin
                            new_ir.lvalue.add_refers_to(refers_to)
                        # Discard Constant
                        # This can happen on yul, like
                        # assembly { var.slot = some_value }
                        # Here we do not keep track of the references as we do not track
                        # such low level manipulation
                        # However we could extend our storage model to do so in the future
                        elif not isinstance(new_ir.rvalue, Constant):
                            new_ir.lvalue.add_refers_to(new_ir.rvalue)

    for succ in node.dominator_successors:
        generate_ssa_irs(
            succ,
            dict(local_variables_instances),
            all_local_variables_instances,
            dict(state_variables_instances),
            all_state_variables_instances,
            init_local_variables_instances,
            visited,
        )

    for dominated in node.dominance_frontier:
        generate_ssa_irs(
            dominated,
            dict(local_variables_instances),
            all_local_variables_instances,
            dict(state_variables_instances),
            all_state_variables_instances,
            init_local_variables_instances,
            visited,
        )


# endregion
###################################################################################
###################################################################################
# region Helpers
###################################################################################
###################################################################################


def last_name(n, var, init_vars):
    candidates = []
    # Todo optimize by creating a variables_ssa_written attribute
    for ir_ssa in n.irs_ssa:
        if isinstance(ir_ssa, OperationWithLValue):
            lvalue = ir_ssa.lvalue
            while isinstance(lvalue, ReferenceVariable):
                lvalue = lvalue.points_to
            if lvalue and lvalue.name == var.name:
                candidates.append(lvalue)
    if n.variable_declaration and n.variable_declaration.name == var.name:
        candidates.append(LocalIRVariable(n.variable_declaration))
    if n.type == NodeType.ENTRYPOINT:
        if var.name in init_vars:
            candidates.append(init_vars[var.name])
    assert candidates
    return max(candidates, key=lambda v: v.index)


def is_used_later(initial_node, variable):
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
# region Update operation
###################################################################################
###################################################################################


def update_lvalue(
    new_ir,
    node,
    local_variables_instances,
    all_local_variables_instances,
    state_variables_instances,
    all_state_variables_instances,
):
    if isinstance(new_ir, OperationWithLValue):
        lvalue = new_ir.lvalue
        update_through_ref = False
        if isinstance(new_ir, (Assignment, Binary)):
            if isinstance(lvalue, ReferenceVariable):
                update_through_ref = True
                while isinstance(lvalue, ReferenceVariable):
                    lvalue = lvalue.points_to
        if isinstance(lvalue, (LocalIRVariable, StateIRVariable)):
            if isinstance(lvalue, LocalIRVariable):
                new_var = LocalIRVariable(lvalue)
                new_var.index = all_local_variables_instances[lvalue.name].index + 1
                all_local_variables_instances[lvalue.name] = new_var
                local_variables_instances[lvalue.name] = new_var
            else:
                new_var = StateIRVariable(lvalue)
                new_var.index = all_state_variables_instances[lvalue.canonical_name].index + 1
                all_state_variables_instances[lvalue.canonical_name] = new_var
                state_variables_instances[lvalue.canonical_name] = new_var
            if update_through_ref:
                phi_operation = Phi(new_var, {node})
                phi_operation.rvalues = [lvalue]
                node.add_ssa_ir(phi_operation)
            if not isinstance(new_ir.lvalue, ReferenceVariable):
                new_ir.lvalue = new_var
            else:
                to_update = new_ir.lvalue
                while isinstance(to_update.points_to, ReferenceVariable):
                    to_update = to_update.points_to
                to_update.points_to = new_var


# endregion
###################################################################################
###################################################################################
# region Initialization
###################################################################################
###################################################################################


def initiate_all_local_variables_instances(
    nodes, local_variables_instances, all_local_variables_instances
):
    for node in nodes:
        if node.variable_declaration:
            new_var = LocalIRVariable(node.variable_declaration)
            if new_var.name in all_local_variables_instances:
                new_var.index = all_local_variables_instances[new_var.name].index + 1
            local_variables_instances[node.variable_declaration.name] = new_var
            all_local_variables_instances[node.variable_declaration.name] = new_var


# endregion
###################################################################################
###################################################################################
# region Phi Operations
###################################################################################
###################################################################################


def fix_phi_rvalues_and_storage_ref(
    node,
    local_variables_instances,
    all_local_variables_instances,
    state_variables_instances,
    all_state_variables_instances,
    init_local_variables_instances,
):
    for ir in node.irs_ssa:
        if isinstance(ir, (Phi)) and not ir.rvalues:
            variables = [
                last_name(dst, ir.lvalue, init_local_variables_instances) for dst in ir.nodes
            ]
            ir.rvalues = variables
        if isinstance(ir, (Phi, PhiCallback)):
            if isinstance(ir.lvalue, LocalIRVariable):
                if ir.lvalue.is_storage:
                    l = [v.refers_to for v in ir.rvalues]
                    l = [item for sublist in l for item in sublist]
                    ir.lvalue.refers_to = set(l)

        if isinstance(ir, (Assignment, Binary)):
            if isinstance(ir.lvalue, ReferenceVariable):
                origin = ir.lvalue.points_to_origin

                if isinstance(origin, LocalIRVariable):
                    if origin.is_storage:
                        for refers_to in origin.refers_to:
                            phi_ir = Phi(refers_to, {node})
                            phi_ir.rvalues = [origin]
                            node.add_ssa_ir(phi_ir)
                            update_lvalue(
                                phi_ir,
                                node,
                                local_variables_instances,
                                all_local_variables_instances,
                                state_variables_instances,
                                all_state_variables_instances,
                            )
    for succ in node.dominator_successors:
        fix_phi_rvalues_and_storage_ref(
            succ,
            dict(local_variables_instances),
            all_local_variables_instances,
            dict(state_variables_instances),
            all_state_variables_instances,
            init_local_variables_instances,
        )


def add_phi_origins(node, local_variables_definition, state_variables_definition):

    # Add new key to local_variables_definition
    # The key is the variable_name
    # The value is (variable_instance, the node where its written)
    # We keep the instance as we want to avoid to add __hash__ on v.name in Variable
    # That might work for this used, but could create collision for other uses
    local_variables_definition = dict(
        local_variables_definition,
        **{v.name: (v, node) for v in node.local_variables_written},
    )
    state_variables_definition = dict(
        state_variables_definition,
        **{v.canonical_name: (v, node) for v in node.state_variables_written},
    )

    # For unini variable declaration
    if (
        node.variable_declaration
        and not node.variable_declaration.name in local_variables_definition
    ):
        local_variables_definition[node.variable_declaration.name] = (
            node.variable_declaration,
            node,
        )

    # filter length of successors because we have node with one successor
    # while most of the ssa textbook would represent following nodes as one
    if node.dominance_frontier and len(node.dominator_successors) != 1:
        for phi_node in node.dominance_frontier:
            for _, (variable, n) in local_variables_definition.items():
                phi_node.add_phi_origin_local_variable(variable, n)
            for _, (variable, n) in state_variables_definition.items():
                phi_node.add_phi_origin_state_variable(variable, n)

    if not node.dominator_successors:
        return
    for succ in node.dominator_successors:
        add_phi_origins(succ, local_variables_definition, state_variables_definition)


# endregion
###################################################################################
###################################################################################
# region IR copy
###################################################################################
###################################################################################


def get(
    variable,
    local_variables_instances,
    state_variables_instances,
    temporary_variables_instances,
    reference_variables_instances,
    tuple_variables_instances,
    all_local_variables_instances,
):
    # variable can be None
    # for example, on LowLevelCall, ir.lvalue can be none
    if variable is None:
        return None
    if isinstance(variable, LocalVariable):
        if variable.name in local_variables_instances:
            return local_variables_instances[variable.name]
        new_var = LocalIRVariable(variable)
        local_variables_instances[variable.name] = new_var
        all_local_variables_instances[variable.name] = new_var
        return new_var
    if isinstance(variable, StateVariable) and variable.canonical_name in state_variables_instances:
        return state_variables_instances[variable.canonical_name]
    if isinstance(variable, ReferenceVariable):
        if not variable.index in reference_variables_instances:
            new_variable = ReferenceVariableSSA(variable)
            if variable.points_to:
                new_variable.points_to = get(
                    variable.points_to,
                    local_variables_instances,
                    state_variables_instances,
                    temporary_variables_instances,
                    reference_variables_instances,
                    tuple_variables_instances,
                    all_local_variables_instances,
                )
            new_variable.set_type(variable.type)
            reference_variables_instances[variable.index] = new_variable
        return reference_variables_instances[variable.index]
    if isinstance(variable, TemporaryVariable):
        if not variable.index in temporary_variables_instances:
            new_variable = TemporaryVariableSSA(variable)
            new_variable.set_type(variable.type)
            temporary_variables_instances[variable.index] = new_variable
        return temporary_variables_instances[variable.index]
    if isinstance(variable, TupleVariable):
        if not variable.index in tuple_variables_instances:
            new_variable = TupleVariableSSA(variable)
            new_variable.set_type(variable.type)
            tuple_variables_instances[variable.index] = new_variable
        return tuple_variables_instances[variable.index]
    assert isinstance(
        variable,
        (
            Constant,
            SolidityVariable,
            Contract,
            Enum,
            SolidityFunction,
            Structure,
            Function,
            Type,
            SolidityImportPlaceHolder,
            TopLevelVariable,
        ),
    )  # type for abi.decode(.., t)
    return variable


def get_variable(ir, f, *instances):
    # pylint: disable=no-value-for-parameter
    variable = f(ir)
    variable = get(variable, *instances)
    return variable


def _get_traversal(values, *instances):
    ret = []
    # pylint: disable=no-value-for-parameter
    for v in values:
        if isinstance(v, list):
            v = _get_traversal(v, *instances)
        else:
            v = get(v, *instances)
        ret.append(v)
    return ret


def get_arguments(ir, *instances):
    return _get_traversal(ir.arguments, *instances)


def get_rec_values(ir, f, *instances):
    # Use by InitArray and NewArray
    # Potential recursive array(s)
    ori_init_values = f(ir)

    return _get_traversal(ori_init_values, *instances)


def copy_ir(ir, *instances):
    """
    Args:
        ir (Operation)
        local_variables_instances(dict(str -> LocalVariable))
        state_variables_instances(dict(str -> StateVariable))
        temporary_variables_instances(dict(int -> Variable))
        reference_variables_instances(dict(int -> Variable))

    Note: temporary and reference can be indexed by int, as they dont need phi functions
    """
    if isinstance(ir, Assignment):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        rvalue = get_variable(ir, lambda x: x.rvalue, *instances)
        variable_return_type = ir.variable_return_type
        return Assignment(lvalue, rvalue, variable_return_type)
    if isinstance(ir, Binary):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        variable_left = get_variable(ir, lambda x: x.variable_left, *instances)
        variable_right = get_variable(ir, lambda x: x.variable_right, *instances)
        operation_type = ir.type
        return Binary(lvalue, variable_left, variable_right, operation_type)
    if isinstance(ir, CodeSize):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        value = get_variable(ir, lambda x: x.value, *instances)
        return CodeSize(value, lvalue)
    if isinstance(ir, Condition):
        val = get_variable(ir, lambda x: x.value, *instances)
        return Condition(val)
    if isinstance(ir, Delete):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        variable = get_variable(ir, lambda x: x.variable, *instances)
        return Delete(lvalue, variable)
    if isinstance(ir, EventCall):
        name = ir.name
        return EventCall(name)
    if isinstance(ir, HighLevelCall):  # include LibraryCall
        destination = get_variable(ir, lambda x: x.destination, *instances)
        function_name = ir.function_name
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        type_call = ir.type_call
        if isinstance(ir, LibraryCall):
            new_ir = LibraryCall(destination, function_name, nbr_arguments, lvalue, type_call)
        else:
            new_ir = HighLevelCall(destination, function_name, nbr_arguments, lvalue, type_call)
        new_ir.call_id = ir.call_id
        new_ir.call_value = get_variable(ir, lambda x: x.call_value, *instances)
        new_ir.call_gas = get_variable(ir, lambda x: x.call_gas, *instances)
        new_ir.arguments = get_arguments(ir, *instances)
        new_ir.function = ir.function
        return new_ir
    if isinstance(ir, Index):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        variable_left = get_variable(ir, lambda x: x.variable_left, *instances)
        variable_right = get_variable(ir, lambda x: x.variable_right, *instances)
        index_type = ir.index_type
        return Index(lvalue, variable_left, variable_right, index_type)
    if isinstance(ir, InitArray):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        init_values = get_rec_values(ir, lambda x: x.init_values, *instances)
        return InitArray(init_values, lvalue)
    if isinstance(ir, InternalCall):
        function = ir.function
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        type_call = ir.type_call
        new_ir = InternalCall(function, nbr_arguments, lvalue, type_call)
        new_ir.arguments = get_arguments(ir, *instances)
        return new_ir
    if isinstance(ir, InternalDynamicCall):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        function = get_variable(ir, lambda x: x.function, *instances)
        function_type = ir.function_type
        new_ir = InternalDynamicCall(lvalue, function, function_type)
        new_ir.arguments = get_arguments(ir, *instances)
        return new_ir
    if isinstance(ir, LowLevelCall):
        destination = get_variable(ir, lambda x: x.destination, *instances)
        function_name = ir.function_name
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        type_call = ir.type_call
        new_ir = LowLevelCall(destination, function_name, nbr_arguments, lvalue, type_call)
        new_ir.call_id = ir.call_id
        new_ir.call_value = get_variable(ir, lambda x: x.call_value, *instances)
        new_ir.call_gas = get_variable(ir, lambda x: x.call_gas, *instances)
        new_ir.arguments = get_arguments(ir, *instances)
        return new_ir
    if isinstance(ir, Member):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        variable_left = get_variable(ir, lambda x: x.variable_left, *instances)
        variable_right = get_variable(ir, lambda x: x.variable_right, *instances)
        return Member(variable_left, variable_right, lvalue)
    if isinstance(ir, NewArray):
        depth = ir.depth
        array_type = ir.array_type
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        new_ir = NewArray(depth, array_type, lvalue)
        new_ir.arguments = get_rec_values(ir, lambda x: x.arguments, *instances)
        return new_ir
    if isinstance(ir, NewElementaryType):
        new_type = ir.type
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        new_ir = NewElementaryType(new_type, lvalue)
        new_ir.arguments = get_arguments(ir, *instances)
        return new_ir
    if isinstance(ir, NewContract):
        contract_name = ir.contract_name
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        new_ir = NewContract(contract_name, lvalue)
        new_ir.arguments = get_arguments(ir, *instances)
        new_ir.call_value = get_variable(ir, lambda x: x.call_value, *instances)
        new_ir.call_salt = get_variable(ir, lambda x: x.call_salt, *instances)
        return new_ir
    if isinstance(ir, NewStructure):
        structure = ir.structure
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        new_ir = NewStructure(structure, lvalue)
        new_ir.arguments = get_arguments(ir, *instances)
        return new_ir
    if isinstance(ir, Nop):
        return Nop()
    if isinstance(ir, Push):
        array = get_variable(ir, lambda x: x.array, *instances)
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        return Push(array, lvalue)
    if isinstance(ir, Return):
        values = get_rec_values(ir, lambda x: x.values, *instances)
        return Return(values)
    if isinstance(ir, Send):
        destination = get_variable(ir, lambda x: x.destination, *instances)
        value = get_variable(ir, lambda x: x.call_value, *instances)
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        return Send(destination, value, lvalue)
    if isinstance(ir, SolidityCall):
        function = ir.function
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        type_call = ir.type_call
        new_ir = SolidityCall(function, nbr_arguments, lvalue, type_call)
        new_ir.arguments = get_arguments(ir, *instances)
        return new_ir
    if isinstance(ir, Transfer):
        destination = get_variable(ir, lambda x: x.destination, *instances)
        value = get_variable(ir, lambda x: x.call_value, *instances)
        return Transfer(destination, value)
    if isinstance(ir, TypeConversion):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        variable = get_variable(ir, lambda x: x.variable, *instances)
        variable_type = ir.type
        return TypeConversion(lvalue, variable, variable_type)
    if isinstance(ir, Unary):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        rvalue = get_variable(ir, lambda x: x.rvalue, *instances)
        operation_type = ir.type
        return Unary(lvalue, rvalue, operation_type)
    if isinstance(ir, Unpack):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        tuple_var = get_variable(ir, lambda x: x.tuple, *instances)
        idx = ir.index
        return Unpack(lvalue, tuple_var, idx)
    if isinstance(ir, Length):
        lvalue = get_variable(ir, lambda x: x.lvalue, *instances)
        value = get_variable(ir, lambda x: x.value, *instances)
        return Length(value, lvalue)

    raise SlithIRError("Impossible ir copy on {} ({})".format(ir, type(ir)))


# endregion
