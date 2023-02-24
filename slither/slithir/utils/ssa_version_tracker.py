from collections import defaultdict
from contextlib import contextmanager
from typing import Iterable

from slither.core.declarations import (
    SolidityVariable,
    Contract,
    Enum,
    SolidityFunction,
    Structure,
    Function,
)
from slither.core.declarations.solidity_import_placeholder import SolidityImportPlaceHolder
from slither.core.solidity_types import Type
from slither.core.variables.local_variable import LocalVariable
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.top_level_variable import TopLevelVariable
from slither.slithir.variables import (
    Constant,
    TemporaryVariableSSA,
    ReferenceVariableSSA,
    StateIRVariable,
    LocalIRVariable,
    TemporaryVariable,
    TupleVariable,
    TupleVariableSSA,
    ReferenceVariable,
)


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

    def __init__(self, vs: "VarStates", variables: Iterable[StateVariable]):
        """Initialize using the set of variables that are of concern
        This class is typically instantiated once per function being translated
        to keep track of StateVar accesses. The idea is to limit which variables
        are kept track of to those actually being read/written by the function.
        """
        self._vs = vs
        self._vars = list(variables)

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
        # would need to have multiple versions? Also check Tuple variables
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

    def state_variables(self) -> Iterable[StateIRVariable]:
        """Returns an iterator to all vars that are of state type"""
        return filter(lambda x: isinstance(x, StateVariable), self._state.keys())

    def _var_to_ir_var(self, v):
        if isinstance(v, LocalVariable):
            return LocalIRVariable(v)
        if isinstance(v, StateVariable):
            return StateIRVariable(v)
        if isinstance(v, TemporaryVariable):
            ssavar = TemporaryVariableSSA(v)
            ssavar.set_type(v.type)
            return ssavar
        if isinstance(v, TupleVariable):
            ssavar = TupleVariableSSA(v)
            ssavar.set_type(v.type)
            return ssavar
        if isinstance(v, ReferenceVariable):
            ssavar = ReferenceVariableSSA(v)
            if v.points_to:
                ssavar.points_to = self.get(v.points_to)
            ssavar.set_type(v.type)
            return ssavar
        assert isinstance(
            v,
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
        return v

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
        captured_state = {
            k: vs.instance_count()
            for (k, vs) in self._state.items()
            if not isinstance(k, StateVariable)
        }
        yield self
        for (k, v) in captured_state.items():
            self._state[k].keep_instances(v)

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
