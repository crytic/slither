import logging

from collections import namedtuple, defaultdict
from slither.core.cfg.node import NodeType
from slither.core.declarations import (Contract, Enum, Function,
                                       SolidityFunction, SolidityVariable,
                                       SolidityVariableComposed, Structure)
from slither.core.solidity_types.type import Type
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import (Assignment, Balance, Binary, Condition,
                                        Delete, EventCall, HighLevelCall,
                                        Index, InitArray, InternalCall,
                                        InternalDynamicCall, Length,
                                        LibraryCall, LowLevelCall, AccessMember,
                                        NewArray, NewContract,
                                        NewElementaryType, NewStructure,
                                        OperationWithLValue, Phi, PhiCallback,
                                        Push, Return, Send, SolidityCall,
                                        Transfer, TypeConversion, Unary,
                                        Unpack, PhiMemberMust, PhiScalar, UpdateMember, UpdateMemberDependency,
                                        PhiMemberMay)
from slither.slithir.variables import (Constant, LocalIRVariable,
                                       IndexVariable, IndexVariableSSA, MemberVariable, MemberVariableSSA,
                                       StateIRVariable, TemporaryVariable,
                                       TemporaryVariableSSA, TupleVariable, TupleVariableSSA)
from slither.slithir.exceptions import SlithIRError

logger = logging.getLogger('SSA_Conversion')


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
    for idx in range(len(tmp_variables)):
        tmp_variables[idx].index = idx
    index_variables = [v for v in variables if isinstance(v, IndexVariable)]
    for idx in range(len(index_variables)):
        index_variables[idx].index = idx
    member_variables = [v for v in variables if isinstance(v, MemberVariable)]
    for idx in range(len(member_variables)):
        member_variables[idx].index = idx
    tuple_variables = [v for v in variables if isinstance(v, TupleVariable)]
    for idx in range(len(tuple_variables)):
        tuple_variables[idx].index = idx


###################################################################################
###################################################################################
# region Instances
###################################################################################
###################################################################################


Instances = namedtuple('Instances', ["local_variables",
                                     "all_local_variables",
                                     "state_variables",
                                     "all_state_variables",
                                     "init_local_variables"])

# instances that live only during the BB, they dont need a fix operators
InstancesTemporary = namedtuple('InstancesTemporary', ['temporary_variables',
                                                       'index_variables',
                                                       'member_variables',
                                                       'tuple_variables'])


# endregion
###################################################################################
###################################################################################
# region SSA conversion
###################################################################################
###################################################################################

def _is_scalar(variable):
    return variable.is_scalar


def add_ssa_ir(function, all_state_variables_instances):
    '''
        Add SSA version of the IR
    Args:
        function
        all_state_variables_instances
    '''

    if not function.is_implemented:
        return

    init_definition = dict()
    for v in function.parameters:
        if v.name:
            init_definition[v.name] = (v, function.entry_point)
            new_var = LocalIRVariable(v)
            function.entry_point.add_ssa_ir(Phi(new_var, set()))

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

    add_phi_origins(function.entry_point, init_definition, dict(), dict())

    for node in function.nodes:
        for (variable, nodes) in node.phi_origins_local_variables.values():
            if len(nodes) < 2:
                continue
            if not is_used_later(node, variable):
                continue
            if _is_scalar(variable):
                node.add_ssa_ir(PhiScalar(LocalIRVariable(variable), nodes))
            else:
                node.add_ssa_ir(Phi(LocalIRVariable(variable), nodes))
        for (variable, nodes) in node.phi_origins_state_variables.values():
            if len(nodes) < 2:
                continue
            # if not is_used_later(node, variable.name, []):
            #    continue
            if _is_scalar(variable):
                node.add_ssa_ir(PhiScalar(StateIRVariable(variable), nodes))
            else:
                node.add_ssa_ir(Phi(StateIRVariable(variable), nodes))
        for (variable, nodes) in node.phi_origin_member_variables.values():
            if len(nodes) < 2:
                continue
            # if not is_used_later(node, variable.name, []):
            #    continue
            if isinstance(variable, LocalVariable):
                cls = LocalIRVariable
            elif isinstance(variable, StateVariable):
                cls = StateIRVariable
            else:
                raise SlithIRError(f'Unkowwn type for phi origin member {variable} ({type(variable)}')
            if _is_scalar(variable):
                node.add_ssa_ir(PhiScalar(cls(variable), nodes))
            else:
                node.add_ssa_ir(Phi(cls(variable), nodes))

    init_local_variables_instances = dict()
    for v in function.parameters:
        if v.name:
            new_var = LocalIRVariable(v)
            function.add_parameter_ssa(new_var)
            if new_var.is_storage:
                fake_variable = LocalIRVariable(v)
                fake_variable.name = 'STORAGE_' + fake_variable.name
                fake_variable.set_location('reference_to_storage')
                new_var.refers_to = {fake_variable}
                init_local_variables_instances[fake_variable.name] = fake_variable
            init_local_variables_instances[v.name] = new_var

    for v in function.returns:
        if v.name:
            new_var = LocalIRVariable(v)
            function.add_return_ssa(new_var)
            if new_var.is_storage:
                fake_variable = LocalIRVariable(v)
                fake_variable.name = 'STORAGE_' + fake_variable.name
                fake_variable.set_location('reference_to_storage')
                new_var.refers_to = {fake_variable}
                init_local_variables_instances[fake_variable.name] = fake_variable
            init_local_variables_instances[v.name] = new_var

    all_init_local_variables_instances = dict(init_local_variables_instances)

    init_state_variables_instances = dict(all_state_variables_instances)

    initiate_all_local_variables_instances(function.nodes, init_local_variables_instances,
                                           all_init_local_variables_instances)

    instances = Instances(dict(init_local_variables_instances),
                          all_init_local_variables_instances,
                          dict(init_state_variables_instances),
                          all_state_variables_instances,
                          init_local_variables_instances)

    generate_ssa_irs(function.entry_point, instances, [])

    # instances = Instances(dict(init_local_variables_instances),
    #                       all_init_local_variables_instances,
    #                       dict(init_state_variables_instances),
    #                       all_state_variables_instances,
    #                       init_local_variables_instances)

    # fix_phi_rvalues_and_storage_ref(function.entry_point, instances)


def generate_ssa_irs(node, instances, visited):
    if node in visited:
        return

    if node.type in [NodeType.ENDIF, NodeType.ENDLOOP] and any(not father in visited for father in node.fathers):
        return

    # visited is shared
    visited.append(node)

    # these variables are lived only during the liveness of the block
    # They dont need phi function
    instances_temporary = InstancesTemporary(dict(), dict(), dict(), dict())
    for ir in node.irs_ssa:
        assert isinstance(ir, Phi)
        update_lvalue(ir, node, instances, instances_temporary)

    for ir in node.irs:

        new_ir = copy_ir(ir, instances, instances_temporary)

        new_ir.set_expression(ir.expression)

        if new_ir:

            node.add_ssa_ir(new_ir)

            update_lvalue(new_ir, node, instances, instances_temporary)

            if isinstance(ir, (InternalCall, HighLevelCall, InternalDynamicCall, LowLevelCall)):
                if isinstance(ir, LibraryCall):
                    continue
                for variable in instances.all_state_variables.values():
                    if not is_used_later(node, variable):
                        continue
                    new_var = StateIRVariable(variable)
                    new_var.index = instances.all_state_variables[variable.canonical_name].index + 1
                    instances.all_state_variables[variable.canonical_name] = new_var
                    instances.state_variables[variable.canonical_name] = new_var
                    phi_ir = PhiCallback(new_var, {node}, new_ir, variable)
                    # rvalues are fixed in solc_parsing.declaration.function
                    node.add_ssa_ir(phi_ir)

            if isinstance(new_ir, (Assignment, Binary)):
                if isinstance(new_ir.lvalue, LocalIRVariable):
                    if new_ir.lvalue.is_storage:
                        # if isinstance(new_ir.rvalue, (IndexVariable, MemberVariable)):
                        #     refers_to = new_ir.rvalue.points_to_origin
                        #     new_ir.lvalue.add_refers_to(refers_to)
                        # else:
                        new_ir.lvalue.add_refers_to(new_ir.rvalue)

    for dom in node.dominance_exploration_ordered:
        new_instances = Instances(dict(instances.local_variables),
                                  instances.all_local_variables,
                                  dict(instances.state_variables),
                                  instances.all_state_variables,
                                  instances.init_local_variables)

        generate_ssa_irs(dom, new_instances, visited)

    # for dominated in node.dominance_frontier:
    #
    #     new_instances = Instances(dict(instances.local_variables),
    #                               instances.all_local_variables,
    #                               dict(instances.state_variables),
    #                               instances.all_state_variables,
    #                               instances.init_local_variables)
    #
    #     generate_ssa_irs(dominated, new_instances, visited)


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
            while isinstance(lvalue, (IndexVariable, MemberVariable)):
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
            if any(v.name == variable.name and v.contract == variable.contract for v in node.state_variables_read):
                return True
            if any(v.name == variable.name and v.contract == variable.contract for v in node.state_variables_written):
                return False
        if isinstance(variable, MemberVariable):
            if any(v.name == variable.name and v.contract == variable.contract for v in node.state_variables_read):
                return True
            if any(v.name == variable.name and v.contract == variable.contract for v in node.state_variables_written):
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

def create_new_var(var, instances, instances_temporary):
    if isinstance(var, LocalIRVariable):
        new_var = LocalIRVariable(var)
        new_var.generate_ssa_phi_info()
        new_var.index = instances.all_local_variables[var.name].index + 1
        instances.all_local_variables[var.name] = new_var
        instances.local_variables[var.name] = new_var
    elif isinstance(var, StateIRVariable):
        new_var = StateIRVariable(var)
        new_var.generate_ssa_phi_info()
        new_var.index = instances.all_state_variables[var.canonical_name].index + 1
        instances.all_state_variables[var.canonical_name] = new_var
        instances.state_variables[var.canonical_name] = new_var
    elif isinstance(var, MemberVariableSSA):
        new_var = MemberVariableSSA(var)
        new_var.generate_ssa_phi_info()
        new_var.index_ssa = var.index_ssa + 1
        if var.points_to:
            new_var.points_to = get(var.points_to, instances, instances_temporary)
        new_var.set_type(var.type)
        new_var.base = get(new_var.base, instances, instances_temporary)
        instances_temporary.member_variables[new_var.index] = new_var
    else:
        raise Exception(f'Unknown {var} type {type(var)}')
    return new_var


def update_lvalue(new_ir, node, instances, instances_temporary):
    update_test(new_ir, node, instances, instances_temporary)

    # update_lvalue_member_variables(new_ir, node, instances)
    # update_lvalue_index_variables(new_ir, node, instances)
    # update_(new_ir, node, instances, instances_temporary)


def update_refers_to(new_ir):
    if isinstance(new_ir.lvalue, LocalIRVariable):
        if new_ir.lvalue.is_storage:
            l = [v.refers_to for v in new_ir.rvalues]
            l = [item for sublist in l for item in sublist]
            new_ir.lvalue.refers_to = set(l)


def create_phi_member(base, member, new_vals, node, instances, instances_temporary, keep_previous=False):
    new_var = create_new_var(base, instances, instances_temporary)

    phi_info = base.ssa_phi_info
    # if keep_previous:
    #     phi_info[str(member)] += new_vals
    # else:
    #     phi_info[str(member)] = new_vals
    phi_info[str(member)] = new_vals

    if keep_previous:
        phi = PhiMemberMay(new_var, {node}, dict(phi_info))
    else:
        phi = PhiMemberMust(new_var, {node}, dict(phi_info))
    phi.rvalues = [base]
    update_refers_to(phi)
    node.add_ssa_ir(phi)

    return new_var


def update_test(new_ir, node, instances, instances_temporary):
    # Update lvalue
    # Main code to create a new SSA var
    if isinstance(new_ir, OperationWithLValue):
        lvalue = new_ir.lvalue

        if isinstance(lvalue, (LocalIRVariable, StateIRVariable)):

            new_var = create_new_var(lvalue, instances, instances_temporary)

            if not isinstance(new_ir.lvalue, (IndexVariable, MemberVariable)):
                new_ir.lvalue = new_var
            else:
                to_update = new_ir.lvalue
                while isinstance(to_update.points_to, (IndexVariable, MemberVariable)):
                    to_update = to_update.points_to
                to_update.points_to = new_var

    # Add phi nodes for UpdateMember operation
    if isinstance(new_ir, UpdateMember):
        # We save new_var, so we know what is the latest member value
        # If the base is a MemberVariableSSa
        new_var = create_phi_member(new_ir.base, new_ir.member, new_ir.new_value,
                                    node, instances, instances_temporary)

        if isinstance(new_ir.base, LocalIRVariable):
            if new_ir.base.is_storage:
                new_var_ = new_var
                for refers_to in new_ir.base.refers_to:
                    if isinstance(refers_to, MemberVariable):
                        new_var = create_phi_member(refers_to.base, refers_to.member, new_var_, node,
                                                    instances, instances_temporary, keep_previous=True)
                    else:
                        new_var = create_phi_member(refers_to, new_ir.member, new_ir.new_value, node,
                                                    instances, instances_temporary, keep_previous=True)

        base = new_ir.base
        while isinstance(base, MemberVariableSSA):
            create_phi_member(base.base, base.member, new_var, node, instances, instances_temporary)
            new_var = base
            base = base.base

    # Update phi rvalues and refers_to
    if isinstance(new_ir, (Phi)) and not new_ir.rvalues:
        variables = [last_name(dst, new_ir.lvalue, instances.init_local_variables) for dst in new_ir.nodes]
        new_ir.rvalues = variables
    if isinstance(new_ir, (Phi, PhiCallback)):
        update_refers_to(new_ir)


def update_(new_ir, node, instances, instances_temporary):
    if isinstance(new_ir, OperationWithLValue):
        lvalue = new_ir.lvalue

        if isinstance(lvalue, (LocalIRVariable, StateIRVariable)):
            if isinstance(lvalue, LocalIRVariable):
                new_var = LocalIRVariable(lvalue)
                new_var.index = instances.all_local_variables[lvalue.name].index + 1
                instances.all_local_variables[lvalue.name] = new_var
                instances.local_variables[lvalue.name] = new_var
            else:
                new_var = StateIRVariable(lvalue)
                new_var.index = instances.all_state_variables[lvalue.canonical_name].index + 1
                instances.all_state_variables[lvalue.canonical_name] = new_var
                instances.state_variables[lvalue.canonical_name] = new_var

            if isinstance(lvalue, MemberVariable):
                member = lvalue.member
                phi_operation = PhiMemberMust(new_var, {node}, member)
                phi_operation.rvalues = [lvalue]
                node.add_ssa_ir(phi_operation)
            elif isinstance(lvalue, IndexVariable):
                phi_operation = Phi(new_var, {node})
                phi_operation.rvalues = [lvalue]
                node.add_ssa_ir(phi_operation)

            if not isinstance(new_ir.lvalue, (IndexVariable, MemberVariable)):
                new_ir.lvalue = new_var
            else:
                to_update = new_ir.lvalue
                while isinstance(to_update.points_to, (IndexVariable, MemberVariable)):
                    to_update = to_update.points_to
                to_update.points_to = new_var


def update_lvalue_member_variables(new_ir, node, instances):
    if isinstance(new_ir, OperationWithLValue):
        lvalue = new_ir.lvalue
        if isinstance(new_ir, (Assignment, Binary)):

            while isinstance(lvalue, MemberVariable):
                member = lvalue.member
                lvalue = lvalue.points_to

                if isinstance(lvalue, (LocalIRVariable, StateIRVariable)):
                    if isinstance(lvalue, LocalIRVariable):
                        new_var = LocalIRVariable(lvalue)
                        new_var.index = instances.all_local_variables[lvalue.name].index + 1
                        instances.all_local_variables[lvalue.name] = new_var
                        instances.local_variables[lvalue.name] = new_var
                    else:
                        new_var = StateIRVariable(lvalue)
                        new_var.index = instances.all_state_variables[lvalue.canonical_name].index + 1
                        instances.all_state_variables[lvalue.canonical_name] = new_var
                        instances.state_variables[lvalue.canonical_name] = new_var

                    phi_operation = PhiMemberMust(new_var, {node}, member)
                    phi_operation.rvalues = [lvalue]
                    node.add_ssa_ir(phi_operation)

                    if not isinstance(new_ir.lvalue, (IndexVariable, MemberVariable)):
                        new_ir.lvalue = new_var
                    else:
                        to_update = new_ir.lvalue
                        while isinstance(to_update.points_to, (IndexVariable, MemberVariable)):
                            to_update = to_update.points_to
                        to_update.points_to = new_var


def update_lvalue_index_variables(new_ir, node, instances):
    if isinstance(new_ir, OperationWithLValue):
        lvalue = new_ir.lvalue
        update_through_ref = False
        if isinstance(new_ir, (Assignment, Binary)):
            if isinstance(lvalue, (IndexVariable)):
                update_through_ref = True
                while isinstance(lvalue, (IndexVariable)):
                    lvalue = lvalue.points_to
        if isinstance(lvalue, (LocalIRVariable, StateIRVariable)):
            if isinstance(lvalue, LocalIRVariable):
                new_var = LocalIRVariable(lvalue)
                new_var.index = instances.all_local_variables[lvalue.name].index + 1
                instances.all_local_variables[lvalue.name] = new_var
                instances.local_variables[lvalue.name] = new_var
            else:
                new_var = StateIRVariable(lvalue)
                new_var.index = instances.all_state_variables[lvalue.canonical_name].index + 1
                instances.all_state_variables[lvalue.canonical_name] = new_var
                instances.state_variables[lvalue.canonical_name] = new_var
            if update_through_ref:
                if _is_scalar(new_var):
                    phi_operation = PhiScalar(new_var, {node})
                else:
                    phi_operation = Phi(new_var, {node})
                phi_operation.rvalues = [lvalue]
                node.add_ssa_ir(phi_operation)
            if not isinstance(new_ir.lvalue, (IndexVariable, MemberVariable)):
                new_ir.lvalue = new_var
            else:
                to_update = new_ir.lvalue
                while isinstance(to_update.points_to, (IndexVariable, MemberVariable)):
                    to_update = to_update.points_to
                to_update.points_to = new_var


# endregion
###################################################################################
###################################################################################
# region Initialization
###################################################################################
###################################################################################

def initiate_all_local_variables_instances(nodes, local_variables_instances, all_local_variables_instances):
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

# TODO unused
def fix_phi_rvalues_and_storage_ref(node, instances):
    for ir in node.irs_ssa:
        if isinstance(ir, (Phi)) and not ir.rvalues:
            variables = [last_name(dst, ir.lvalue, instances.init_local_variables) for dst in ir.nodes]
            ir.rvalues = variables
        if isinstance(ir, (Phi, PhiCallback)):
            if isinstance(ir.lvalue, LocalIRVariable):
                if ir.lvalue.is_storage:
                    l = [v.refers_to for v in ir.rvalues]
                    l = [item for sublist in l for item in sublist]
                    ir.lvalue.refers_to = set(l)

        if isinstance(ir, (Assignment, Binary)):
            if isinstance(ir.lvalue, (IndexVariable, MemberVariable)):
                origin = ir.lvalue.points_to_origin

                if isinstance(origin, LocalIRVariable):
                    if origin.is_storage:
                        for refers_to in origin.refers_to:
                            if _is_scalar(refers_to):
                                phi_ir = PhiScalar(refers_to, {node})
                            else:
                                phi_ir = Phi(refers_to, {node})
                            phi_ir.rvalues = [origin]
                            node.add_ssa_ir(phi_ir)
                            update_lvalue(phi_ir, node, instances, InstancesTemporary(dict(), dict(), dict(), dict()))
    for succ in node.dominator_successors:
        new_instances = Instances(dict(instances.local_variables),
                                  instances.all_local_variables,
                                  dict(instances.state_variables),
                                  instances.all_state_variables,
                                  instances.init_local_variables)
        fix_phi_rvalues_and_storage_ref(succ, new_instances)


def add_phi_origins(node, local_variables_definition, state_variables_definition, member_variables_definition):
    # Add new key to local_variables_definition
    # The key is the variable_name 
    # The value is (variable_instance, the node where its written)
    # We keep the instance as we want to avoid to add __hash__ on v.name in Variable
    # That might work for this used, but could create collision for other uses
    local_variables_definition = dict(local_variables_definition,
                                      **{v.name: (v, node) for v in node.local_variables_written})
    state_variables_definition = dict(state_variables_definition,
                                      **{v.canonical_name: (v, node) for v in node.state_variables_written})

    member_variables_definition = dict(member_variables_definition,
                                       **{v.name: (v, node) for v in [(ir.base) for ir
                                                                      in node.irs if isinstance(ir, UpdateMember)]})

    # For unini variable declaration
    if node.variable_declaration and \
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
            for _, (variable, n) in member_variables_definition.items():
                phi_node.add_phi_origin_member_variable(variable, n)

    if not node.dominator_successors:
        return
    for succ in node.dominator_successors:
        add_phi_origins(succ, local_variables_definition, state_variables_definition, member_variables_definition)


# endregion
###################################################################################
###################################################################################
# region IR copy
###################################################################################
###################################################################################

def get(variable, instances, instances_temporary):
    # variable can be None
    # for example, on LowLevelCall, ir.lvalue can be none
    if variable is None:
        return None
    if isinstance(variable, LocalVariable):
        if variable.name in instances.local_variables:
            return instances.local_variables[variable.name]
        new_var = LocalIRVariable(variable)
        instances.local_variables[variable.name] = new_var
        instances.all_local_variables[variable.name] = new_var
        return new_var
    if isinstance(variable, StateVariable) and variable.canonical_name in instances.state_variables:
        return instances.state_variables[variable.canonical_name]
    elif isinstance(variable, IndexVariable):
        if not variable.index in instances_temporary.index_variables:
            new_variable = IndexVariableSSA(variable)
            if variable.points_to:
                new_variable.points_to = get(variable.points_to, instances, instances_temporary)
            new_variable.set_type(variable.type)
            instances_temporary.index_variables[variable.index] = new_variable
        return instances_temporary.index_variables[variable.index]
    elif isinstance(variable, MemberVariable):
        if not variable.index in instances_temporary.member_variables:
            new_variable = MemberVariableSSA(variable)
            if variable.points_to:
                new_variable.points_to = get(variable.points_to, instances, instances_temporary)
            new_variable.set_type(variable.type)
            new_variable.base = get(variable.base, instances, instances_temporary)
            instances_temporary.member_variables[variable.index] = new_variable
        return instances_temporary.member_variables[variable.index]
    elif isinstance(variable, TemporaryVariable):
        if not variable.index in instances_temporary.temporary_variables:
            new_variable = TemporaryVariableSSA(variable)
            new_variable.set_type(variable.type)
            instances_temporary.temporary_variables[variable.index] = new_variable
        return instances_temporary.temporary_variables[variable.index]
    elif isinstance(variable, TupleVariable):
        if not variable.index in instances_temporary.tuple_variables:
            new_variable = TupleVariableSSA(variable)
            new_variable.set_type(variable.type)
            instances_temporary.tuple_variables[variable.index] = new_variable
        return instances_temporary.tuple_variables[variable.index]
    assert isinstance(variable, (Constant,
                                 SolidityVariable,
                                 Contract,
                                 Enum,
                                 SolidityFunction,
                                 Structure,
                                 Function,
                                 Type))  # type for abi.decode(.., t)
    return variable


def get_variable(ir, f, instances, instances_temporary):
    variable = f(ir)
    variable = get(variable, instances, instances_temporary)
    return variable


def _get_traversal(values, instances, instances_temporary):
    ret = []
    for v in values:
        if isinstance(v, list):
            v = _get_traversal(v, instances, instances_temporary)
        else:
            v = get(v, instances, instances_temporary)
        ret.append(v)
    return ret


def get_arguments(ir, instances, instances_temporary):
    return _get_traversal(ir.arguments, instances, instances_temporary)


def get_rec_values(ir, f, instances, instances_temporary):
    # Use by InitArray and NewArray
    # Potential recursive array(s)
    ori_init_values = f(ir)

    return _get_traversal(ori_init_values, instances, instances_temporary)


def copy_ir(ir, instances, instances_temporary):
    '''

    Note: temporary and reference can be indexed by int, as they dont need phi functions
    '''
    if isinstance(ir, Assignment):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        rvalue = get_variable(ir, lambda x: x.rvalue, instances, instances_temporary)
        variable_return_type = ir.variable_return_type
        return Assignment(lvalue, rvalue, variable_return_type)
    elif isinstance(ir, Balance):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        value = get_variable(ir, lambda x: x.value, instances, instances_temporary)
        return Balance(value, lvalue)
    elif isinstance(ir, Binary):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        variable_left = get_variable(ir, lambda x: x.variable_left, instances, instances_temporary)
        variable_right = get_variable(ir, lambda x: x.variable_right, instances, instances_temporary)
        operation_type = ir.type
        return Binary(lvalue, variable_left, variable_right, operation_type)
    elif isinstance(ir, Condition):
        val = get_variable(ir, lambda x: x.value, instances, instances_temporary)
        return Condition(val)
    elif isinstance(ir, Delete):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        variable = get_variable(ir, lambda x: x.variable, instances, instances_temporary)
        return Delete(lvalue, variable)
    elif isinstance(ir, EventCall):
        name = ir.name
        return EventCall(name)
    elif isinstance(ir, HighLevelCall):  # include LibraryCall
        destination = get_variable(ir, lambda x: x.destination, instances, instances_temporary)
        function_name = ir.function_name
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        type_call = ir.type_call
        if isinstance(ir, LibraryCall):
            new_ir = LibraryCall(destination, function_name, nbr_arguments, lvalue, type_call)
        else:
            new_ir = HighLevelCall(destination, function_name, nbr_arguments, lvalue, type_call)
        new_ir.call_id = ir.call_id
        new_ir.call_value = get_variable(ir, lambda x: x.call_value, instances, instances_temporary)
        new_ir.call_gas = get_variable(ir, lambda x: x.call_gas, instances, instances_temporary)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        new_ir.function = ir.function
        return new_ir
    elif isinstance(ir, Index):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        variable_left = get_variable(ir, lambda x: x.variable_left, instances, instances_temporary)
        variable_right = get_variable(ir, lambda x: x.variable_right, instances, instances_temporary)
        index_type = ir.index_type
        return Index(lvalue, variable_left, variable_right, index_type)
    elif isinstance(ir, InitArray):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        init_values = get_rec_values(ir, lambda x: x.init_values, instances, instances_temporary)
        return InitArray(init_values, lvalue)
    elif isinstance(ir, InternalCall):
        function = ir.function
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        type_call = ir.type_call
        new_ir = InternalCall(function, nbr_arguments, lvalue, type_call)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, InternalDynamicCall):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        function = get_variable(ir, lambda x: x.function, instances, instances_temporary)
        function_type = ir.function_type
        new_ir = InternalDynamicCall(lvalue, function, function_type)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, LowLevelCall):
        destination = get_variable(ir, lambda x: x.destination, instances, instances_temporary)
        function_name = ir.function_name
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        type_call = ir.type_call
        new_ir = LowLevelCall(destination, function_name, nbr_arguments, lvalue, type_call)
        new_ir.call_id = ir.call_id
        new_ir.call_value = get_variable(ir, lambda x: x.call_value, instances, instances_temporary)
        new_ir.call_gas = get_variable(ir, lambda x: x.call_gas, instances, instances_temporary)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, AccessMember):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        variable_left = get_variable(ir, lambda x: x.variable_left, instances, instances_temporary)
        variable_right = get_variable(ir, lambda x: x.variable_right, instances, instances_temporary)
        return AccessMember(variable_left, variable_right, lvalue)
    elif isinstance(ir, UpdateMember):
        base = get_variable(ir, lambda x: x.base, instances, instances_temporary)
        member = ir.member
        new_value = get_variable(ir, lambda x: x.new_value, instances, instances_temporary)
        return UpdateMember(base, member, new_value)
    elif isinstance(ir, UpdateMemberDependency):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        base = get_variable(ir, lambda x: x.base, instances, instances_temporary)
        member = ir.member
        new_value = get_variable(ir, lambda x: x.new_value, instances, instances_temporary)
        return UpdateMemberDependency(base, member, new_value, lvalue)
    elif isinstance(ir, NewArray):
        depth = ir.depth
        array_type = ir.array_type
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        new_ir = NewArray(depth, array_type, lvalue)
        new_ir.arguments = get_rec_values(ir, lambda x: x.arguments, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, NewElementaryType):
        new_type = ir.type
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        new_ir = NewElementaryType(new_type, lvalue)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, NewContract):
        contract_name = ir.contract_name
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        new_ir = NewContract(contract_name, lvalue)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, NewStructure):
        structure = ir.structure
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        new_ir = NewStructure(structure, lvalue)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, Push):
        array = get_variable(ir, lambda x: x.array, instances, instances_temporary)
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        return Push(array, lvalue)
    elif isinstance(ir, Return):
        values = get_rec_values(ir, lambda x: x.values, instances, instances_temporary)
        return Return(values)
    elif isinstance(ir, Send):
        destination = get_variable(ir, lambda x: x.destination, instances, instances_temporary)
        value = get_variable(ir, lambda x: x.call_value, instances, instances_temporary)
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        return Send(destination, value, lvalue)
    elif isinstance(ir, SolidityCall):
        function = ir.function
        nbr_arguments = ir.nbr_arguments
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        type_call = ir.type_call
        new_ir = SolidityCall(function, nbr_arguments, lvalue, type_call)
        new_ir.arguments = get_arguments(ir, instances, instances_temporary)
        return new_ir
    elif isinstance(ir, Transfer):
        destination = get_variable(ir, lambda x: x.destination, instances, instances_temporary)
        value = get_variable(ir, lambda x: x.call_value, instances, instances_temporary)
        return Transfer(destination, value)
    elif isinstance(ir, TypeConversion):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        variable = get_variable(ir, lambda x: x.variable, instances, instances_temporary)
        variable_type = ir.type
        return TypeConversion(lvalue, variable, variable_type)
    elif isinstance(ir, Unary):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        rvalue = get_variable(ir, lambda x: x.rvalue, instances, instances_temporary)
        operation_type = ir.type
        return Unary(lvalue, rvalue, operation_type)
    elif isinstance(ir, Unpack):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        tuple_var = get_variable(ir, lambda x: x.tuple, instances, instances_temporary)
        idx = ir.index
        return Unpack(lvalue, tuple_var, idx)
    elif isinstance(ir, Length):
        lvalue = get_variable(ir, lambda x: x.lvalue, instances, instances_temporary)
        value = get_variable(ir, lambda x: x.value, instances, instances_temporary)
        return Length(value, lvalue)

    raise SlithIRError('Impossible ir copy on {} ({})'.format(ir, type(ir)))

# endregion
