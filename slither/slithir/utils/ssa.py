from slither.slithir.variables import (Constant, ReferenceVariable,
                                       TemporaryVariable, TupleVariable)
from slither.slithir.operations import OperationWithLValue, Phi
from slither.slithir.variables import LocalIRVariable

def transform_slithir_vars_to_ssa(function):
    """
        Transform slithIR vars to SSA
    """
    variables = []
    for node in function.nodes:
        for ir in node.irs:
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

def add_phi_operations(function):
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
            n = list(nodes)[0]
            variable = next((v for v in n.variables_written if v.name == variable_name), None)
            if variable is None:
                variable = n.variable_declaration
            node.add_pre_ir(Phi(LocalIRVariable(variable), nodes))

    init_local_variables_counter = dict()
    for v in function.parameters+function.returns:
        if v.name:
            init_local_variables_counter[v.name] = 0
    init_global_variables_counter = dict(init_local_variables_counter)
    rename_variables(function.entry_point, init_local_variables_counter, init_global_variables_counter)

    fix_phi_operations(function.nodes)

def fix_phi_operations(nodes):
    def last_name(n, var):
        candidates = [v for v in n.variables_written if v.name == var.name]
        if n.variable_declaration and n.variable_declaration.name == var.name:
            candidates.append(LocalIRVariable(n.variable_declaration))
        assert candidates
        return max(candidates, key=lambda v: v.index)

    for node in nodes:
        for ir in node.irs:
            if isinstance(ir, Phi):
                variables = [last_name(dst, ir.lvalue) for dst in ir.nodes]
                ir.rvalues = variables

def rename_variables(node, local_variables_counter, global_variables_counter):

    if node.variable_declaration:
        local_variables_counter[node.variable_declaration.name] = 0
        global_variables_counter[node.variable_declaration.name] = 0

    for idx in range(len(node.irs)):
        ir = node.irs[idx]
        for used in ir.used:
            if isinstance(used, LocalIRVariable):
                used.index = local_variables_counter[used.name]

        if isinstance(ir, OperationWithLValue):
            if isinstance(ir.lvalue, LocalIRVariable):
                counter = global_variables_counter[ir.lvalue.name]
                counter = counter + 1
                global_variables_counter[ir.lvalue.name] = counter
                local_variables_counter[ir.lvalue.name] = counter
                ir.lvalue.index = counter

    for succ in node.dominator_successors:
        rename_variables(succ, dict(local_variables_counter), global_variables_counter)

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



def transform_localir_vars_to_ssa(function):
    """
        Transform slithIR vars to SSA
    """
    pass
