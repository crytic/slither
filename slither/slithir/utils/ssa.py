import logging

from slither.core.cfg.node import NodeType
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.operations import (Assignment, Balance, Binary,
                                        BinaryType, Condition, Delete,
                                        EventCall, HighLevelCall, Index,
                                        InitArray, InternalCall,
                                        InternalDynamicCall, Length,
                                        LibraryCall, LowLevelCall, Member,
                                        NewArray, NewContract,
                                        NewElementaryType, NewStructure,
                                        OperationWithLValue, Phi, Push, Return,
                                        Send, SolidityCall, Transfer,
                                        TypeConversion, Unary, Unpack)
from slither.slithir.variables import (Constant, LocalIRVariable,
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

def add_ssa_ir(function):
    '''
        Add SSA version of the IR
    '''

    if not function.is_implemented:
        return

    init_definition = dict()
    for v in function.parameters+function.returns:
        if v.name:
            init_definition[v.name] = function.entry_point
    add_phi_origins(function.entry_point, init_definition)

    for node in function.nodes:
        for variable_name, nodes in node.phi_origins.items():
            if len(nodes)<2 :
                continue
            # assumption: at this level we can retrieve 
            # an instance of the variable
            # by looking at the variables written
            # of any of the nodes
            for n in nodes:
                variable = next((v for v in n.variables_written if v.name == variable_name), None)
                if variable is None:
                    variable = n.variable_declaration
                if variable:
                    break
            assert variable
            node.add_ssa_ir(Phi(LocalIRVariable(variable), nodes))

    init_local_variables_instances = dict()
    for v in function.parameters+function.returns:
        if v.name:
            init_local_variables_instances[v.name] = LocalIRVariable(v)
    init_global_variables_instances = dict(init_local_variables_instances)
    generate_ssa_irs(function.entry_point,
                     dict(init_local_variables_instances),
                     init_global_variables_instances)

    fix_phi_operations(function.nodes, init_local_variables_instances)


def fix_phi_operations(nodes, init_vars):
    def last_name(n, var):
        candidates = []
        # Todo optimize by creating a variables_ssa_written attribute
        for ir_ssa in n.irs_ssa:
            if isinstance(ir_ssa, OperationWithLValue):
                if ir_ssa.lvalue and ir_ssa.lvalue.name == var.name:
                    candidates.append(ir_ssa.lvalue)
        if n.variable_declaration and n.variable_declaration.name == var.name:
            candidates.append(LocalIRVariable(n.variable_declaration))
        if n.type == NodeType.ENTRYPOINT:
            if var.name in init_vars:
                candidates.append(init_vars[var.name])
        assert candidates
        return max(candidates, key=lambda v: v.index)

    for node in nodes:
        for ir in node.irs_ssa:
            if isinstance(ir, Phi):
                variables = [last_name(dst, ir.lvalue) for dst in ir.nodes]
                ir.rvalues = variables

def generate_ssa_irs(node, local_variables_instances, global_variables_instances):

    if node.variable_declaration:
        new_var = LocalIRVariable(node.variable_declaration)
        local_variables_instances[node.variable_declaration.name] = new_var
        global_variables_instances[node.variable_declaration.name] = new_var

    for ir in node.irs:
#        ir = node.irs[idx]
#        for used in ir.used:
#            if isinstance(used, LocalIRVariable):
#                used.index = local_variables_instances[used.name]
        new_ir = copy_ir(ir, local_variables_instances)
        if new_ir:
            node.add_ssa_ir(new_ir)

        if isinstance(new_ir, OperationWithLValue):
            if isinstance(new_ir.lvalue, LocalIRVariable):
                new_var = LocalIRVariable(new_ir.lvalue)
                new_var.index = global_variables_instances[new_ir.lvalue.name].index + 1
                global_variables_instances[new_ir.lvalue.name] = new_var
                local_variables_instances[new_ir.lvalue.name] = new_var
                new_ir.lvalue = new_var

    for succ in node.dominator_successors:
        generate_ssa_irs(succ, dict(local_variables_instances), global_variables_instances)

def add_phi_origins(node, variables_definition):

    # Add new key to variables_definition
    # the key is the variable_name and the value the node where its written
    variables_definition = dict(variables_definition,
                                **{v.name: node for v in node.variables_written})

    # For unini variable declaration
    if node.variable_declaration and\
       not node.variable_declaration.name in variables_definition:
        variables_definition[node.variable_declaration.name] = node

    # filter len of successors because we have node with one successors
    # while most of the ssa textbook would represent following nodes as one
    if node.dominance_frontier and len(node.dominator_successors) != 1:
        for phi_node in node.dominance_frontier:
            for variable_name, n in variables_definition.items():
                phi_node.add_phi_origin(variable_name, n)

    if not node.dominator_successors:
        return
    for succ in node.dominator_successors:
        add_phi_origins(succ, variables_definition)

def copy_ir(ir, variables_instances):
    '''
    Args:
        ir (Operation)
        variables_instances(dict(str -> Variable))
    '''

    def get_variable(ir, f):
        variable = f(ir)
        if isinstance(variable, LocalVariable) and variable.name in variables_instances:
            variable = variables_instances[variable.name]
        return variable

    def get_arguments(ir):
        arguments = []
        for arg in ir.arguments:
            if isinstance(arg, LocalVariable) and arg.name in variables_instances:
                arg = variables_instances[arg.name]
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
                    if isinstance(v, LocalVariable) and v.name in variables_instances:
                        v = variables_instances[v.name]
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
        value = get_variable(ir, lambda x: ir.value)
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

