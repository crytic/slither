import logging

from slither.core.cfg.node import NodeType
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import (Assignment, Balance, Binary,
                                        BinaryType, Condition, Delete,
                                        EventCall, HighLevelCall, Index,
                                        InitArray, InternalCall,
                                        InternalDynamicCall, Length,
                                        LibraryCall, LowLevelCall, Member,
                                        NewArray, NewContract,
                                        NewElementaryType, NewStructure,
                                        OperationWithLValue, Phi, PhiCallback, Push, Return,
                                        Send, SolidityCall, Transfer,
                                        TypeConversion, Unary, Unpack)
from slither.slithir.variables import (Constant, LocalIRVariable, StateIRVariable,
                                       ReferenceVariable, TemporaryVariable,
                                       TupleVariable)

logger = logging.getLogger('SSA_Conversion')



def transform_slithir_vars_to_ssa(function):
    """
        Transform slithIR vars to SSA
    """
    variables = []
    for node in function.nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, OperationWithLValue) and not ir.lvalue in variables:
                variables += [ir.lvalue]

    tmp_variables = [v for v in variables if isinstance(v, TemporaryVariable)]
    for idx in range(len(tmp_variables)):
        tmp_variables[idx].index = idx
    ref_variables = [v for v in variables if isinstance(v, ReferenceVariable)]
    for idx in range(len(ref_variables)):
        ref_variables[idx].index = idx
    tuple_variables = [v for v in variables if isinstance(v, TupleVariable)]
    for idx in range(len(tuple_variables)):
        tuple_variables[idx].index = idx

def add_ssa_ir(function, all_state_variables_instances, all_state_variables_written):
    '''
        Add SSA version of the IR
    Args:
        function
        all_state_variables_instances
        all_state_variables_written (set(str)): canonical name of all the state variables written
    '''

    if not function.is_implemented:
        return

    init_definition = dict()
    for v in function.parameters+function.returns:
        if v.name:
            new_var = LocalIRVariable(v)
            print(new_var.name)
            print(new_var.is_storage)
            if new_var.is_storage:
                new_var.points_to = {v}
            init_definition[new_var.name] = (new_var, function.entry_point)

    # We only add phi function for state variable at entry node if
    # The state variable is used
    # And if the state variables is written in another function (otherwise its stay at index 0)
    for (canonical_name, variable_instance) in all_state_variables_instances.items():
        if is_used_later(function.entry_point, variable_instance, []):
#            and canonical_name in all_state_variables_written:
            # rvalues are fixed in solc_parsing.declaration.function
            function.entry_point.add_ssa_ir(Phi(StateIRVariable(variable_instance), set()))

    add_phi_origins(function.entry_point, init_definition, dict())


    for node in function.nodes:
        for (variable, nodes) in node.phi_origins_local_variables.values():
            if len(nodes)<2:
                continue
            if not is_used_later(node, variable, []):
                continue
            node.add_ssa_ir(Phi(LocalIRVariable(variable), nodes))
        for (variable, nodes) in node.phi_origins_state_variables.values():
            if len(nodes)<2:
                continue
            #if not is_used_later(node, variable.name, []):
            #    continue
            node.add_ssa_ir(Phi(StateIRVariable(variable), nodes))

    init_local_variables_instances = dict()
    for v in function.parameters+function.returns:
        if v.name:
            init_local_variables_instances[v.name] = LocalIRVariable(v)
    all_init_local_variables_instances = dict(init_local_variables_instances)

    init_state_variables_instances = dict(all_state_variables_instances)

    generate_ssa_irs(function.entry_point,
                     dict(init_local_variables_instances),
                     all_init_local_variables_instances,
                     dict(init_state_variables_instances),
                     all_state_variables_instances,
                     init_local_variables_instances,
                     [])

    #fix_phi_operations(function.nodes, init_local_variables_instances)

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

def fix_phi_operations(nodes, init_vars):
    def last_name(n, var):
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

    for node in nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, Phi) and not ir.rvalues:
                variables = [last_name(dst, ir.lvalue) for dst in ir.nodes]
                ir.rvalues = variables

def update_lvalue(new_ir, node, local_variables_instances, all_local_variables_instances, state_variables_instances, all_state_variables_instances):
    if isinstance(new_ir, OperationWithLValue):
        lvalue = new_ir.lvalue
        update_through_ref = False
        if isinstance(new_ir, Assignment):
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

def is_used_later(node, variable, visited):
    # TODO: does not handle the case where its read and written in the declaration node
    # It can be problematic if this happens in a loop/if structure
    # Ex:
    # for(;true;){
    #   if(true){
    #     uint a = a;
    #    }
    #     ..
    if node in visited:
        return False
    # shared visited
    visited.append(node)
    if isinstance(variable, LocalVariable):
        if any(v.name == variable.name for v in node.local_variables_read):
            return True
        if any(v.name == variable.name for v in node.local_variables_written):
            return False
    if isinstance(variable, StateVariable):
        if any(v.name == variable.name and v.contract == variable.contract for v in node.state_variables_read):
            return True
        if any(v.name == variable.name and v.contract == variable.contract for v in node.state_variables_written):
            return False
    return any(is_used_later(son, variable, visited) for son in node.sons)

def generate_ssa_irs(node, local_variables_instances, all_local_variables_instances, state_variables_instances, all_state_variables_instances, init_local_variables_instances, visited):

    if node in visited:
        return

    if node.fathers and any(not father in visited for father in node.fathers):
        return

    # visited is shared
    visited.append(node)

    if node.variable_declaration:
        new_var = LocalIRVariable(node.variable_declaration)
        local_variables_instances[node.variable_declaration.name] = new_var
        all_local_variables_instances[node.variable_declaration.name] = new_var

    for ir in node.irs_ssa:
        assert isinstance(ir, Phi)
        update_lvalue(ir, node, local_variables_instances, all_local_variables_instances, state_variables_instances, all_state_variables_instances)

    for ir in node.irs:
        new_ir = copy_ir(ir, local_variables_instances, state_variables_instances)
        update_lvalue(new_ir, node, local_variables_instances, all_local_variables_instances, state_variables_instances, all_state_variables_instances)

        if new_ir:

            node.add_ssa_ir(new_ir)
            if isinstance(ir, (InternalCall, HighLevelCall, InternalDynamicCall, LowLevelCall)):
                if isinstance(ir, LibraryCall):
                    continue
                for variable in all_state_variables_instances.values():
                    if not is_used_later(node, variable, []):
                        continue
                    new_var = StateIRVariable(variable)
                    new_var.index = all_state_variables_instances[variable.canonical_name].index + 1
                    all_state_variables_instances[variable.canonical_name] = new_var
                    state_variables_instances[variable.canonical_name] = new_var
                    phi_ir = PhiCallback(new_var, {node}, new_ir, variable)
                    # rvalues are fixed in solc_parsing.declaration.function
                    node.add_ssa_ir(phi_ir)

            if isinstance(new_ir, Assignment):
                if isinstance(new_ir.lvalue, LocalIRVariable):
                    if new_ir.lvalue.is_storage:
                        new_ir.lvalue.add_points_to(new_ir.rvalue)

    for ir in node.irs_ssa:
        if isinstance(ir, (Phi)) and not ir.rvalues:
            variables = [last_name(dst, ir.lvalue, init_local_variables_instances) for dst in ir.nodes]
            ir.rvalues = variables
        if isinstance(ir, (Phi, PhiCallback)):
            if isinstance(ir.lvalue, LocalIRVariable):
                if ir.lvalue.is_storage:
                    l = [v.points_to for v in ir.rvalues]
                    l = [item for sublist in l for item in sublist]
                    ir.lvalue.points_to = set(l)

        if isinstance(ir, Assignment):
            if isinstance(ir.lvalue, ReferenceVariable):
                origin = ir.lvalue.points_to_origin

                if isinstance(origin, LocalIRVariable):
                    if origin.is_storage:
                        for points_to in origin.points_to:
                            phi_ir = Phi(points_to, {node})
                            phi_ir.rvalues = [origin]
                            node.add_ssa_ir(phi_ir)
                            update_lvalue(phi_ir, node, local_variables_instances, all_local_variables_instances, state_variables_instances, all_state_variables_instances)


    for succ in node.dominator_successors:
        generate_ssa_irs(succ, dict(local_variables_instances), all_local_variables_instances, dict(state_variables_instances), all_state_variables_instances, init_local_variables_instances, visited)

    for dominated in node.dominance_frontier:
        generate_ssa_irs(dominated, dict(local_variables_instances), all_local_variables_instances, dict(state_variables_instances), all_state_variables_instances, init_local_variables_instances, visited)

def add_phi_origins(node, local_variables_definition, state_variables_definition):

    # Add new key to local_variables_definition
    # The key is the variable_name 
    # The value is (variable_instance, the node where its written)
    # We keep the instance as we want to avoid to add __hash__ on v.name in Variable
    # That might work for this used, but could create collision for other uses
    local_variables_definition = dict(local_variables_definition,
                                **{v.name: (v, node) for v in node.local_variables_written})
    state_variables_definition = dict(state_variables_definition,
                                **{v.canonical_name: (v, node) for v in node.state_variables_written})

    # For unini variable declaration
    if node.variable_declaration and\
       not node.variable_declaration.name in local_variables_definition:
        local_variables_definition[node.variable_declaration.name] = (node.variable_declaration, node)

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

def copy_ir(ir, local_variables_instances, state_variables_instances):
    '''
    Args:
        ir (Operation)
        variables_instances(dict(str -> Variable))
    '''

    def get(variable):
        if isinstance(variable, LocalVariable) and variable.name in local_variables_instances:
            return local_variables_instances[variable.name]
        if isinstance(variable, StateVariable) and variable.canonical_name in state_variables_instances:
            return state_variables_instances[variable.canonical_name]
        elif isinstance(variable, ReferenceVariable):
            new_variable = ReferenceVariable(variable.node, index=variable.index)
            if variable.points_to:
                new_variable.points_to = get(variable.points_to)
            new_variable.set_type(variable.type)
            return new_variable
        elif isinstance(variable, TemporaryVariable):
            new_variable = TemporaryVariable(variable.node, index=variable.index)
            new_variable.set_type(variable.type)
            return new_variable
        return variable

    def get_variable(ir, f):
        variable = f(ir)
        variable = get(variable)
        return variable

    def get_arguments(ir):
        arguments = []
        for arg in ir.arguments:
            arg = get(arg)
            arguments.append(arg)
        return arguments

    def get_rec_values(ir, f):
        # Use by InitArray and NewArray
        # Potential recursive array(s)
        ori_init_values = f(ir)

        def traversal(values):
            ret = []
            for v in values:
                if isinstance(v, list):
                    v = traversal(v)
                else:
                    v = get(v)
                ret.append(v)
            return ret

        return traversal(ori_init_values)


    if isinstance(ir, Assignment):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        rvalue = get_variable(ir, lambda x: ir.rvalue)
        variable_return_type = ir.variable_return_type
        return Assignment(lvalue, rvalue, variable_return_type)
    elif isinstance(ir, Balance):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        value = get_variable(ir, lambda x: ir.value)
        return Balance(value, lvalue)
    elif isinstance(ir, Binary):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        variable_left = get_variable(ir, lambda x: ir.variable_left)
        variable_right = get_variable(ir, lambda x: ir.variable_right)
        operation_type = ir.type
        return Binary(lvalue, variable_left, variable_right, operation_type)
    elif isinstance(ir, Condition):
        val = get_variable(ir, lambda x: ir.value)
        return Condition(val)
    elif isinstance(ir, Delete):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        variable = get_variable(ir, lambda x: ir.variable)
        return Delete(lvalue, variable)
    elif isinstance(ir, EventCall):
        name = ir.name
        return EventCall(name)
    elif isinstance(ir, HighLevelCall): # include LibraryCall
        destination = get_variable(ir, lambda x: ir.destination)
        function_name = ir.function_name
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        type_call = ir.type_call
        if isinstance(ir, LibraryCall):
            new_ir = LibraryCall(destination, function_name, nbr_arguments, lvalue, type_call)
        else:
            new_ir = HighLevelCall(destination, function_name, nbr_arguments, lvalue, type_call)
        new_ir.call_id = ir.call_id
        new_ir.call_value = get_variable(ir, lambda x: ir.call_value)
        new_ir.call_gas = get_variable(ir, lambda x: ir.call_gas)
        new_ir.arguments = get_arguments(ir)
        new_ir.function_instance = ir.function
        return new_ir
    elif isinstance(ir, Index):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        variable_left = get_variable(ir, lambda x: ir.variable_left)
        variable_right = get_variable(ir, lambda x: ir.variable_right)
        index_type = ir.index_type
        return Index(lvalue, variable_left, variable_right, index_type)
    elif isinstance(ir, InitArray):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        init_values = get_rec_values(ir, lambda x: ir.init_values)
        return InitArray(init_values, lvalue)
    elif isinstance(ir, InternalCall):
        function = ir.function
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        type_call = ir.type_call
        new_ir = InternalCall(function, nbr_arguments, lvalue, type_call)
        new_ir.arguments = get_arguments(ir)
        return new_ir
    elif isinstance(ir, InternalDynamicCall):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        function = ir.function
        function_type = ir.function_type
        new_ir = InternalDynamicCall(lvalue, function, function_type)
        new_ir.arguments = get_arguments(ir)
        return new_ir
    elif isinstance(ir, LowLevelCall):
        destination = get_variable(ir, lambda x: x.destination)
        function_name = ir.function_name
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        type_call = ir.type_call
        new_ir = LowLevelCall(destination, function_name, nbr_arguments, lvalue, type_call)
        new_ir.call_id = ir.call_id
        new_ir.call_value = get_variable(ir, lambda x: ir.call_value)
        new_ir.call_gas = get_variable(ir, lambda x: ir.call_gas)
        new_ir.arguments = get_arguments(ir)
        return new_ir
    elif isinstance(ir, Member):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        variable_left = get_variable(ir, lambda x: ir.variable_left)
        variable_right = get_variable(ir, lambda x: ir.variable_right)
        return Member(variable_left, variable_right, lvalue)
    elif isinstance(ir, NewArray):
        depth = ir.depth
        array_type = ir.array_type
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        new_ir = NewArray(depth, array_type, lvalue)
        new_ir.arguments = get_rec_values(ir, lambda x: ir.arguments)
        return new_ir
    elif isinstance(ir, NewElementaryType):
        new_type = ir.type
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        new_ir = NewElementaryType(new_type, lvalue)
        new_ir.arguments = get_arguments(ir)
        return new_ir
    elif isinstance(ir, NewContract):
        contract_name = ir.contract_name
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        new_ir = NewContract(contract_name, lvalue)
        new_ir.arguments = get_arguments(ir)
        return new_ir
    elif isinstance(ir, NewStructure):
        structure = ir.structure
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        new_ir = NewStructure(structure, lvalue)
        new_ir.arguments = get_arguments(ir)
        return new_ir
    elif isinstance(ir, Push):
        array = get_variable(ir, lambda x: ir.array)
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        return Push(array, lvalue)
    elif isinstance(ir, Return):
        value = get_variable(ir, lambda x: ir.values)
        return Return(value)
    elif isinstance(ir, Send):
        destination = get_variable(ir, lambda x: ir.destination)
        value = get_variable(ir, lambda x: ir.call_value)
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        return Send(destination, value, lvalue)
    elif isinstance(ir, SolidityCall):
        function = ir.function
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        type_call = ir.type_call
        new_ir = SolidityCall(function, nbr_arguments, lvalue, type_call)
        new_ir.arguments = get_arguments(ir)
        return new_ir
    elif isinstance(ir, Transfer):
        destination = get_variable(ir, lambda x: ir.destination)
        value = get_variable(ir, lambda x: ir.call_value)
        return Transfer(destination, value)
    elif isinstance(ir, TypeConversion):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        variable = get_variable(ir, lambda x: ir.variable)
        variable_type = ir.type
        return TypeConversion(lvalue, variable, variable_type)
    elif isinstance(ir, Unary):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        rvalue = get_variable(ir, lambda x: ir.rvalue)
        operation_type = ir.type
        return Unary(lvalue, rvalue, operation_type)
    elif isinstance(ir, Unpack):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        tuple_var = ir.tuple
        idx = ir.index
        return Unpack(lvalue, tuple_var, idx)
    elif isinstance(ir, Length):
        lvalue = get_variable(ir, lambda x: ir.lvalue)
        value = get_variable(ir, lambda x: ir.value)
        return Length(value, lvalue)


    logger.error('Impossible ir copy on {} ({})'.format(ir, type(ir)))
    exit(-1)

def transform_localir_vars_to_ssa(function):
    """
        Transform slithIR vars to SSA
    """
    pass

