import logging
from collections import defaultdict
from contextlib import contextmanager
from functools import cmp_to_key
from typing import Union, Iterator, Iterable, Set, Tuple

from build.lib.slither.slithir.variables import tuple
from slither.core.cfg.node import NodeType, Node
from slither.core.declarations import (
    Contract,
    Enum,
    Function,
    SolidityFunction,
    SolidityVariable,
    Structure,
)
from slither.core.declarations.function import FunctionType
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
    Nop, Operation,
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

class StateVarDefRecorder:
    """
    Captures information about StateVariable definitions at different points in a function
    are current at different stages for a function.

    Overview of the idea:
    For a StateVariable, sv, its current SSA-defs at end of function (including return
    statements) is recorded. Before any call the SSA-defs for sv is also recorded. Then,
    to populate the phi-nodes at entry the following rvalues are used:

    sv_1 = phi(sv_0, Union(SSA-defs at function exit), Union(SSA-defs before all calls)

    This records the three states a StateVariable can be in at function entry:
    1. Uninitialized (sv_0)
    2. Whatever states some other function writing to it left it in
    3. For reentrant calls, the state before the call for any call

    If a function uses sv after a call, a phi node is placed after call:

    sv_n = phi(sv_n-1, Union(Union(SSA-defs at function exit))

    This records the two states a StateVariable can be in after the call
    1. The state before the call (no change when invoking function)
    2. Some other function completed and modified the state, hence any exit state

    """
    def __init__(self, vs: "VarStates", vars: Iterable[StateVariable]):
        """Initialize using the set of variables that are of concern

        This class is typically instantiated once per function being translated
        to keep track of StateVar accesses. The idea is to limit which variables
        are kept track of to those actually being read/written by the function.
        """
        self._vs = vs
        self._vars = list(vars)

    def collect_before_call(self):
        """Collect the defs active at time of a call

        Calls the VarStates to register the current version of each var of concern
        with the 'at_call' state.
        """
        for sv in self._vars:
            self._vs.register_at_call(sv)

    def collect_at_end(self):
        """Collect the defs active at end of function

        Calls the VarStates to register the current version of each var of concern
        with the 'at_end' state.
        """
        for sv in self._vars:
            self._vs.register_at_end(sv)

class VarState:
    def __init__(self):
        self.index = 0
        self.instances = []

    def append(self, ir_var):
        """
        Adds a new instance/version of an SSA variable to the current working set

        The odd birds here are the TemporaryVariableSSA and ReferenceVariableSSA
        which already is indexed (in SSA form) and should not be incremented.
        """
        # TODO (hbrodin): Is it correct? Are there any occasions where a temporary variable
        # would need to have multiple versions?
        if not isinstance(ir_var, (TemporaryVariableSSA, ReferenceVariableSSA)):
            ir_var.index = self.index
            self.index += 1
        self.instances.append(ir_var)

    def instance_count(self) -> int:
        """Returns how many versions/instances there are of variable"""
        return len(self.instances)

    def keep_instances(self, n):
        """Drop all but the n first instances"""
        self.instances = self.instances[:n]
        return self


class VarStates:
    def __init__(self):
        self._state = defaultdict(VarState)
        self._func_defs = {}
        self._state_vars_at_end = defaultdict(set)
        self._state_vars_entry_phi = defaultdict(set)

    def register_at_call(self, sv: StateVariable):
        """Register a StateVariable last definition as current at time of call"""
        sv_ir = self.get(sv)
        self._state_vars_entry_phi[sv].add(sv_ir)

    def register_at_end(self, sv: StateVariable):
        """Register a StateVariable last definition as current at time of call"""
        sv_ir = self.get(sv)
        self._state_vars_at_end[sv].add(sv_ir)
        self._state_vars_entry_phi[sv].add(sv_ir)

    def add(self, v):
        """Adds a new definition of v, creates a new version"""
        if v is None or isinstance(v, Constant):
            return None

        ir_var = self._var_to_ir_var(v)
        self._state[v].append(ir_var)
        return ir_var

    def get(self, v):
        """Returns the current ssa version of the var v

        If no version exists - that is this is is the first time an argument,
        return or global variable is referenced - a new ssa version is created
        and returned.
        """
        if v is None or isinstance(v, Constant):
            return v
        if v not in self._state:
            return self.add(v)
        return self._state[v].instances[-1]

    def state_variables(self) -> Iterator[StateIRVariable]:
        """Returns an iterator to all vars that are of state type"""
        return filter(lambda x: isinstance(x, StateVariable), self._state.keys())

    def _var_to_ir_var(self, v):
        if isinstance(v, LocalVariable):
            return LocalIRVariable(v)
        elif isinstance(v, StateVariable):
            return StateIRVariable(v)
        elif isinstance(v, TemporaryVariable):
            ssavar = TemporaryVariableSSA(v)
            ssavar.set_type(v.type)
            return ssavar
        elif isinstance(v, TupleVariable):
            ssavar = TupleVariableSSA(v)
            ssavar.set_type(v.type)
            return ssavar
        elif isinstance(v, ReferenceVariable):
            ssavar = ReferenceVariableSSA(v)
            if v.points_to:
                ssavar.points_to = self.get(v.points_to)
            ssavar.set_type(v.type)
            return ssavar
        raise SlithIRError(f"Unknown variable type{v}")

    @contextmanager
    def new_scope(self):
        """Produces a new scope for the variables

        This is part of the algorithm for assigning labels/versions/indices
        to variables in ssa-form. Any successor in the dominator tree builds
        on the naming from this node, but they each have their own naming
        scopes (can't share vars between them).

        The one exception implemented here is that StateVariables are not
        restored to previous state. Those are global, every new definition
        of a state variable (assignemnt to it) creates a new version, within
        the scope of the VarStates (typically for a Contract).
        """
        captured_state = {k: vs.instance_count() for (k, vs) in self._state.items() if not isinstance(k, StateVariable)}
        yield self
        [self._state[k].keep_instances(v) for (k, v) in captured_state.items()]

    def compute_entry_phis(self):
        """Compute the entry point phi-values for each StateVariable

        Entrypoint phi-values are: a union of:
         - all last defs before call, and
         - the last def when leaving a function for all functions, and
         - the initial value for those Variables
        """
        for (k, v) in self._state_vars_entry_phi.items():
            v.add(self._state[k].instances[0])
        return self._state_vars_entry_phi

    def end_states(self):
        return self._state_vars_at_end

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
            new_ir = LibraryCall(destination, ir.function_name, ir.nbr_arguments, lvalue, ir.type_call)
        else:
            new_ir = HighLevelCall(destination, ir.function_name, ir.nbr_arguments, lvalue, ir.type_call)
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
    if isinstance(ir, Push):
        array = get_ssa(ir.array)
        lvalue = add_def(ir.lvalue)
        return Push(array, lvalue)
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
        print(f"Conversion of {variable} ({ir.variable}) to {lvalue} ({ir.lvalue})")
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

    raise SlithIRError("Impossible ir copy on {} ({})".format(ir, type(ir)))

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
    def add(vars, addfunc):
        for var in filter(lambda x: x.name, vars):
            # Get the initial version and record it in the function
            ssa0 = ssa_state.add(var)

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
    if function.function_type in (FunctionType.CONSTRUCTOR_VARIABLES,
                                  FunctionType.CONSTRUCTOR_CONSTANT_VARIABLES):
        abort = False

    if abort:
        return

    if ssa_state is None:
        ssa_state = VarStates()

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
    add_phi_origins(function.nodes, ssa_state)

    # Transform IR to SSA ir by cloning IR nodes and add version info. This will also
    # append Phi-nodes after external calls (for any state variable currently used).
    ir_nodes_to_ssa(function.entry_point, ssa_state, rec)

    # Collect the final state of variables at the end of function
    # calls will have been made at points where a Return operation
    # was found as well.
    rec.collect_at_end()

    return

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

def referenced_state_variables(function: Function) -> Set[StateVariable]:
    """Returns a set of all StateVariables that are referenced in a function"""
    vars = set()
    for node in function.nodes:
        vars.update(node.state_variables_written)
        vars.update(node.state_variables_read)
    return vars

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


def _add_dummy_phi(node, var: Union[LocalVariable, StateVariable]):
    """Produces a dummy phi for when the real def can't be determined

    Before all phi-functions have been placed it is not possible to tell
    which node defines a variable for a phi. This function creates dummy
    phi information using the predecessor node. It could be the correct
    node, but it could also be a parent node in the dominator tree. See
    the _find_var_def function for lookups.
    """
    func = (
        node.add_phi_origin_local_variable
        if isinstance(var, LocalVariable)
        else node.add_phi_origin_state_variable
    )
    for predecessor in node.fathers:
        func(var, predecessor)


def _find_var_def(node, var: Union[LocalVariable, StateVariable]):
    """Find the real definition of a variable

    When placing dummy-phi functions origin of a value is
    set to the predecessors of a node with a phi-function.
    The actual value might be defined in parent in the
    dominator tree. Walk the tree towards the root to find
    which node either writes var or is assigned phi-node
    for it.
    """
    # print(f"Find def {node} for {var}")
    is_local_var = isinstance(var, LocalVariable)
    while node:
        if is_local_var:
            if var in node.local_variables_written:
                # print(f"\tvar is written in {node}")
                return node
            if var.name in node.phi_origins_local_variables.keys():
                # print(f"\tvar is phi in {node}")
                return node
        else:
            # Assumes StateVariable
            if var in node.state_variables_written:
                # print(f"\tstate var is written in {node}")
                return node
            if var.name in node.phi_origins_state_variables.keys():
                # print(f"\tstate var is phi in {node}")
                return node
        if not node.immediate_dominator:
            # If node becomes none we are at the entry point, and it is already assigned
            # the phi-node for this var
            # print("\tvar is entrypoint {node}")
            return node

        node = node.immediate_dominator


def add_phi_origins(nodes, vars):
    """Insert Phi-nodes where needed"""
    # Phase 1 place dummy phi nodes
    workset = set()
    all_phi = set()
    for node in filter(lambda n: n.dominance_frontier, nodes):
        for phi_node in node.dominance_frontier:
            workset.add(phi_node)
            all_phi.add(phi_node)
            for local_var in node.local_variables_written:
                _add_dummy_phi(phi_node, local_var)

            for state_var in node.state_variables_written:
                _add_dummy_phi(phi_node, state_var)

    # Phase 2 - any phi-node is a 'def' and should thus be propagated. Iter until no change.
    while workset:
        node = workset.pop()
        for phi_node in node.dominance_frontier:
            for (local_var, _) in node.phi_origins_local_variables.values():
                if local_var.name not in phi_node.phi_origins_local_variables:
                    _add_dummy_phi(phi_node, local_var)
                    workset.add(phi_node)
                    all_phi.add(phi_node)

            for (state_var, _) in node.phi_origins_state_variables.values():
                if state_var.name not in phi_node.phi_origins_state_variables:
                    _add_dummy_phi(phi_node, state_var)
                    workset.add(phi_node)
                    all_phi.add(phi_node)

    # Phase 3 - now that all phi nodes are recorded with dummy info (partially) lets add Phi IRs
    for node in all_phi:
        for (variable, source_nodes) in node.phi_origins_local_variables.values():
            if len(source_nodes) < 2:
                # TODO (hbrodin): How do we report errors/inconsistencies?
                print("Unexpected no need for a phi node if < 2 predecessors")
                continue

            # TODO (hbrodin): Make sure this is correct
            # if not is_used_later(node, variable):
            #   continue
            nodes_real_origin = set(map(lambda n, var=variable: _find_var_def(n, var), source_nodes))
            node.add_ssa_ir(Phi(LocalIRVariable(variable), nodes_real_origin))
            #node.add_ssa_ir(Phi(variable, nodes_real_origin))
            #node.add_ssa_ir(Phi(_add_ir_var(vars, variable), set()))
        for (variable, source_nodes) in node.phi_origins_state_variables.values():
            if len(source_nodes) < 2:
                # TODO (hbrodin): How do we report errors/inconsistencies?
                print("Unexpected no need for a phi node if < 2 predecessors")
                continue

            # TODO (hbrodin): Make sure this is correct
            # if not is_used_later(node, variable.name, []):
            #    continue
            nodes_real_origin = set(map(lambda n, var=variable: _find_var_def(n, var), source_nodes))
            node.add_ssa_ir(Phi(StateIRVariable(variable), nodes_real_origin))
            #node.add_ssa_ir(Phi(variable, nodes_real_origin))
            #node.add_ssa_ir(Phi(_add_ir_var(vars, variable), set()))




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

    raise SlithIRError(f"Impossible ir copy on {ir} ({type(ir)})")

# endregion
