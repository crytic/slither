import os
import pathlib
from argparse import ArgumentTypeError
from collections import defaultdict
from contextlib import contextmanager
from inspect import getsourcefile
from tempfile import NamedTemporaryFile
from typing import Union, List, Optional

import pytest
from solc_select import solc_select
from solc_select.solc_select import valid_version as solc_valid_version

from slither import Slither
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function, Contract
from slither.core.variables.state_variable import StateVariable
from slither.slithir.operations import (
    OperationWithLValue,
    Phi,
    Assignment,
    HighLevelCall,
    Return,
    Operation,
    Binary,
    BinaryType,
    InternalCall,
)
from slither.slithir.utils.ssa import is_used_later
from slither.slithir.variables import Constant, ReferenceVariable, LocalIRVariable, StateIRVariable


# Directory of currently executing script. Will be used as basis for temporary file names.
SCRIPT_DIR = pathlib.Path(getsourcefile(lambda: 0)).parent


def valid_version(ver: str) -> bool:
    """Wrapper function to check if the solc-version is valid

    The solc_select function raises and exception but for checks below,
    only a bool is needed.
    """
    try:
        solc_valid_version(ver)
        return True
    except ArgumentTypeError:
        return False


def have_ssa_if_ir(function: Function):
    """Verifies that all nodes in a function that have IR also have SSA IR"""
    for n in function.nodes:
        if n.irs:
            assert n.irs_ssa


# pylint: disable=too-many-branches
def ssa_basic_properties(function: Function):
    """Verifies that basic properties of ssa holds

    1. Every name is defined only once
    2. A l-value is never index zero - there is always a zero-value available for each var
    3. Every r-value is at least defined at some point
    4. The number of ssa defs is >= the number of assignments to var
    5. Function parameters SSA are stored in function.parameters_ssa
       - if function parameter is_storage it refers to a fake variable
    6. Function returns SSA are stored in function.returns_ssa
        - if function return is_storage it refers to a fake variable
    """
    ssa_lvalues = set()
    ssa_rvalues = set()
    lvalue_assignments = {}

    for n in function.nodes:
        for ir in n.irs:
            if isinstance(ir, OperationWithLValue):
                name = ir.lvalue.name
                if name in lvalue_assignments:
                    lvalue_assignments[name] += 1
                else:
                    lvalue_assignments[name] = 1

        for ssa in n.irs_ssa:
            if isinstance(ssa, OperationWithLValue):
                # 1
                assert ssa.lvalue not in ssa_lvalues
                ssa_lvalues.add(ssa.lvalue)

                # 2 (if Local/State Var)
                if isinstance(ssa.lvalue, (StateIRVariable, LocalIRVariable)):
                    assert ssa.lvalue.index > 0

            for rvalue in filter(
                lambda x: not isinstance(x, (StateIRVariable, Constant)), ssa.read
            ):
                ssa_rvalues.add(rvalue)

    # 3
    # Each var can have one non-defined value, the value initially held. Typically,
    # var_0, i_0, state_0 or similar.
    undef_vars = set()
    for rvalue in ssa_rvalues:
        if rvalue not in ssa_lvalues:
            assert rvalue.non_ssa_version not in undef_vars
            undef_vars.add(rvalue.non_ssa_version)

    # 4
    ssa_defs = defaultdict(int)
    for v in ssa_lvalues:
        ssa_defs[v.name] += 1

    for (k, n) in lvalue_assignments.items():
        assert ssa_defs[k] >= n

    # Helper 5/6
    def check_property_5_and_6(variables, ssavars):
        for var in filter(lambda x: x.name, variables):
            ssa_vars = [x for x in ssavars if x.non_ssa_version == var]
            assert len(ssa_vars) == 1
            ssa_var = ssa_vars[0]
            assert var.is_storage == ssa_var.is_storage
            if ssa_var.is_storage:
                assert len(ssa_var.refers_to) == 1
                assert ssa_var.refers_to[0].location == "reference_to_storage"

    # 5
    check_property_5_and_6(function.parameters, function.parameters_ssa)

    # 6
    check_property_5_and_6(function.returns, function.returns_ssa)


def ssa_phi_node_properties(f: Function):
    """Every phi-function should have as many args as predecessors

    This does not apply if the phi-node refers to state variables,
    they make use os special phi-nodes for tracking potential values
    a state variable can have
    """
    for node in f.nodes:
        for ssa in node.irs_ssa:
            if isinstance(ssa, Phi):
                n = len(ssa.read)
                if not isinstance(ssa.lvalue, StateIRVariable):
                    assert len(node.fathers) == n


# TODO (hbrodin): This should probably go into another file, not specific to SSA
def dominance_properties(f: Function):
    """Verifies properties related to dominators holds

    1. Every node have an immediate dominator except entry_node which have none
    2. From every node immediate dominator there is a path via its successors to the node
    """

    def find_path(from_node: Node, to: Node) -> bool:
        visited = set()
        worklist = list(from_node.sons)
        while worklist:
            first, *worklist = worklist
            if first == to:
                return True
            visited.add(first)
            for successor in first.sons:
                if successor not in visited:
                    worklist.append(successor)
        return False

    for node in f.nodes:
        if node is f.entry_point:
            assert node.immediate_dominator is None
        else:
            assert node.immediate_dominator is not None
            assert find_path(node.immediate_dominator, node)


def phi_values_inserted(f: Function):
    """Verifies that phi-values are inserted at the right places

    For every node that has a dominance frontier, any def (including
    phi) should be a phi function in its dominance frontier
    """

    def have_phi_for_var(node: Node, var):
        """Checks if a node has a phi-instruction for var

        The ssa version would ideally be checked, but then
        more data flow analysis would be needed, for cases
        where a new def for var is introduced before reaching
        DF
        """
        non_ssa = var.non_ssa_version
        for ssa in node.irs_ssa:
            if isinstance(ssa, Phi):
                if non_ssa in map(lambda ssa_var: ssa_var.non_ssa_version, ssa.read):
                    return True
        return False

    for node in filter(lambda n: n.dominance_frontier, f.nodes):
        for df in node.dominance_frontier:
            for ssa in node.irs_ssa:
                if isinstance(ssa, OperationWithLValue):
                    if is_used_later(node, ssa.lvalue):
                        assert have_phi_for_var(df, ssa.lvalue)


@contextmanager
def select_solc_version(version: Optional[str]):
    """Selects solc version to use for running tests.

    If no version is provided, latest is used."""
    # If no solc_version selected just use the latest avail
    if not version:
        # This sorts the versions numerically
        vers = sorted(
            map(
                lambda x: (int(x[0]), int(x[1]), int(x[2])),
                map(lambda x: x.split(".", 3), solc_select.installed_versions()),
            )
        )
        ver = list(vers)[-1]
        version = ".".join(map(str, ver))
    env = dict(os.environ)
    env_restore = dict(env)
    env["SOLC_VERSION"] = version
    os.environ.clear()
    os.environ.update(env)

    yield version

    os.environ.clear()
    os.environ.update(env_restore)


@contextmanager
def slither_from_source(source_code: str, solc_version: Optional[str] = None):
    """Yields a Slither instance using source_code string and solc_version

    Creates a temporary file and changes the solc-version temporary to solc_version.
    """

    fname = ""
    try:
        with NamedTemporaryFile(dir=SCRIPT_DIR, mode="w", suffix=".sol", delete=False) as f:
            fname = f.name
            f.write(source_code)
        with select_solc_version(solc_version):
            yield Slither(fname)
    finally:
        pathlib.Path(fname).unlink()


def verify_properties_hold(source_code_or_slither: Union[str, Slither]):
    """Ensures that basic properties of SSA hold true"""

    def verify_func(func: Function):
        have_ssa_if_ir(func)
        phi_values_inserted(func)
        ssa_basic_properties(func)
        ssa_phi_node_properties(func)
        dominance_properties(func)

    def verify(slither):
        for cu in slither.compilation_units:
            for func in cu.functions_and_modifiers:
                _dump_function(func)
                verify_func(func)
            for contract in cu.contracts:
                for f in contract.functions:
                    if f.is_constructor or f.is_constructor_variables:
                        _dump_function(f)
                        verify_func(f)

    if isinstance(source_code_or_slither, Slither):
        verify(source_code_or_slither)
    else:
        with slither_from_source(source_code_or_slither) as slither:
            verify(slither)


def _dump_function(f: Function):
    """Helper function to print nodes/ssa ir for a function or modifier"""
    print(f"---- {f.name} ----")
    for n in f.nodes:
        print(n)
        for ir in n.irs_ssa:
            print(f"\t{ir}")
    print("")


def _dump_functions(c: Contract):
    """Helper function to print functions and modifiers of a contract"""
    for f in c.functions_and_modifiers:
        _dump_function(f)


def get_filtered_ssa(f: Union[Function, Node], flt) -> List[Operation]:
    """Returns a list of all ssanodes filtered by filter for all nodes in function f"""
    if isinstance(f, Function):
        return [ssanode for node in f.nodes for ssanode in node.irs_ssa if flt(ssanode)]

    assert isinstance(f, Node)
    return [ssanode for ssanode in f.irs_ssa if flt(ssanode)]


def get_ssa_of_type(f: Union[Function, Node], ssatype) -> List[Operation]:
    """Returns a list of all ssanodes of a specific type for all nodes in function f"""
    return get_filtered_ssa(f, lambda ssanode: isinstance(ssanode, ssatype))


def test_multi_write():
    contract = """
    pragma solidity ^0.8.11;
    contract Test {
    function multi_write(uint val) external pure returns(uint) {
        val = 1;
        val = 2;
        val = 3;
    }
    }"""
    verify_properties_hold(contract)


def test_single_branch_phi():
    contract = """
        pragma solidity ^0.8.11;
        contract Test {
        function single_branch_phi(uint val) external pure returns(uint) {
            if (val == 3) {
                val = 9;
            }
            return val;
        }
        }
        """
    verify_properties_hold(contract)


def test_basic_phi():
    contract = """
    pragma solidity ^0.8.11;
    contract Test {
    function basic_phi(uint val) external pure returns(uint) {
        if (val == 3) {
            val = 9;
        } else {
            val = 1;
        }
        return val;
    }
    }
    """
    verify_properties_hold(contract)


def test_basic_loop_phi():
    contract = """
    pragma solidity ^0.8.11;
    contract Test {
    function basic_loop_phi(uint val) external pure returns(uint) {
        for (uint i=0;i<128;i++) {
            val = val + 1;
        }
        return val;
    }
    }
    """
    verify_properties_hold(contract)


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_phi_propagation_loop():
    contract = """
     pragma solidity ^0.8.11;
     contract Test {
     function looping(uint v) external pure returns(uint) {
        uint val = 0;
        for (uint i=0;i<v;i++) {
            if (val > i) {
                val = i;
            } else {
                val = 3;
            }
        }
        return val;
    }
    }
    """
    verify_properties_hold(contract)


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_free_function_properties():
    contract = """
        pragma solidity ^0.8.11;

        function free_looping(uint v) returns(uint) {
           uint val = 0;
           for (uint i=0;i<v;i++) {
               if (val > i) {
                   val = i;
               } else {
                   val = 3;
               }
           }
           return val;
       }

       contract Test {}
       """
    verify_properties_hold(contract)


def test_ssa_inter_transactional():
    source = """
    pragma solidity ^0.8.11;
    contract A {
        uint my_var_A;
        uint my_var_B;

        function direct_set(uint i) public {
            my_var_A = i;
        }

        function direct_set_plus_one(uint i) public {
            my_var_A = i + 1;
        }

        function indirect_set() public {
            my_var_B = my_var_A;
        }
    }
    """
    with slither_from_source(source) as slither:
        c = slither.contracts[0]
        variables = c.variables_as_dict
        funcs = c.available_functions_as_dict()
        direct_set = funcs["direct_set(uint256)"]
        # Skip entry point and go straight to assignment ir
        assign1 = direct_set.nodes[1].irs_ssa[0]
        assert isinstance(assign1, Assignment)

        assign2 = direct_set.nodes[1].irs_ssa[0]
        assert isinstance(assign2, Assignment)

        indirect_set = funcs["indirect_set()"]
        phi = indirect_set.entry_point.irs_ssa[0]
        assert isinstance(phi, Phi)
        # phi rvalues come from 1, initial value of my_var_a and 2, assignment in direct_set
        assert len(phi.rvalues) == 3
        assert all(x.non_ssa_version == variables["my_var_A"] for x in phi.rvalues)
        assert assign1.lvalue in phi.rvalues
        assert assign2.lvalue in phi.rvalues


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_ssa_phi_callbacks():
    source = """
    pragma solidity ^0.8.11;
    contract A {
        uint my_var_A;
        uint my_var_B;

        function direct_set(uint i) public {
            my_var_A = i;
        }

        function use_a() public {
            // Expect a phi-node here
            my_var_B = my_var_A;
            B b = new B();
            my_var_A = 3;
            b.do_stuff();
            // Expect a phi-node here
            my_var_B = my_var_A;
        }
    }

    contract B {
        function do_stuff() public returns (uint) {
            // This could be calling back into A
        }
    }
    """
    with slither_from_source(source) as slither:
        c = slither.get_contract_from_name("A")[0]
        _dump_functions(c)
        f = [x for x in c.functions if x.name == "use_a"][0]
        var_a = [x for x in c.variables if x.name == "my_var_A"][0]

        entry_phi = [
            x
            for x in f.entry_point.irs_ssa
            if isinstance(x, Phi) and x.lvalue.non_ssa_version == var_a
        ][0]
        # The four potential sources are:
        # 1. initial value
        # 2. my_var_A = i;
        # 3. my_var_A = 3;
        # 4. phi-value after call to b.do_stuff(), which could be reentrant.
        assert len(entry_phi.rvalues) == 4

        # Locate the first high-level call (should be b.do_stuff())
        call_node = [x for y in f.nodes for x in y.irs_ssa if isinstance(x, HighLevelCall)][0]
        n = call_node.node
        # Get phi-node after call
        after_call_phi = n.irs_ssa[n.irs_ssa.index(call_node) + 1]
        # The two sources for this phi node is
        # 1. my_var_A = i;
        # 2. my_var_A = 3;
        assert isinstance(after_call_phi, Phi)
        assert len(after_call_phi.rvalues) == 2


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_storage_refers_to():
    """Test the storage aspects of the SSA IR

    When declaring a var as being storage, start tracking what storage it refers_to.
    When a phi-node is created, ensure refers_to is propagated to the phi-node.
    Assignments also propagate refers_to.
    Whenever a ReferenceVariable is the destination of an assignment (e.g. s.v = 10)
    below, create additional versions of the variables it refers to record that a a
    write was made. In the current implementation, this is referenced by phis.
    """
    source = """
   contract A{

    struct St{
        int v;
    }

    St state0;
    St state1;

    function f() public{
        St storage s = state0;
        if(true){
            s = state1;
        }
        s.v = 10;
    }
}
    """
    with slither_from_source(source) as slither:
        c = slither.contracts[0]
        f = c.functions[0]

        phinodes = get_ssa_of_type(f, Phi)
        # Expect 2 in entrypoint (state0/state1 initial values), 1 at 'ENDIF' and two related to the
        # ReferenceVariable write s.v = 10.
        assert len(phinodes) == 5

        # Assign s to state0, s to state1, s.v to 10
        assigns = get_ssa_of_type(f, Assignment)
        assert len(assigns) == 3

        # The IR variables have is_storage
        assert all(x.lvalue.is_storage for x in assigns if isinstance(x, LocalIRVariable))

        # s.v ReferenceVariable points to one of the phi vars...
        ref0 = [x.lvalue for x in assigns if isinstance(x.lvalue, ReferenceVariable)][0]
        sphis = [x for x in phinodes if x.lvalue == ref0.points_to]
        assert len(sphis) == 1
        sphi = sphis[0]

        # ...and that phi refers to the two entry phi-values
        entryphi = [x for x in phinodes if x.lvalue in sphi.lvalue.refers_to]
        assert len(entryphi) == 2

        # The remaining two phis are the ones recording that write through ReferenceVariable occured
        for ephi in entryphi:
            phinodes.remove(ephi)
        phinodes.remove(sphi)
        assert len(phinodes) == 2

        # And they are recorded in one of the entry phis
        assert phinodes[0].lvalue in entryphi[0].rvalues or entryphi[1].rvalues
        assert phinodes[1].lvalue in entryphi[0].rvalues or entryphi[1].rvalues


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
@pytest.mark.skipif(
    not valid_version("0.4.0"), reason="Solidity version 0.4.0 not available on this platform"
)
def test_initial_version_exists_for_locals():
    """
    In solidity you can write statements such as
    uint a = a + 1, this test ensures that can be handled for local variables.
    """
    src = """
    contract C {
        function func() internal {
            uint a = a + 1;
        }
    }
    """
    with slither_from_source(src, "0.4.0") as slither:
        verify_properties_hold(slither)
        c = slither.contracts[0]
        f = c.functions[0]

        addition = get_ssa_of_type(f, Binary)[0]
        assert addition.type == BinaryType.ADDITION
        assert isinstance(addition.variable_right, Constant)
        a_0 = addition.variable_left
        assert a_0.index == 0
        assert a_0.name == "a"

        assignment = get_ssa_of_type(f, Assignment)[0]
        a_1 = assignment.lvalue
        assert a_1.index == 1
        assert a_1.name == "a"
        assert assignment.rvalue == addition.lvalue

        assert a_0.non_ssa_version == a_1.non_ssa_version


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
@pytest.mark.skipif(
    not valid_version("0.4.0"), reason="Solidity version 0.4.0 not available on this platform"
)
def test_initial_version_exists_for_state_variables():
    """
    In solidity you can write statements such as
    uint a = a + 1, this test ensures that can be handled for state variables.
    """
    src = """
    contract C {
        uint a = a + 1;
    }
    """
    with slither_from_source(src, "0.4.0") as slither:
        verify_properties_hold(slither)
        c = slither.contracts[0]
        f = c.functions[0]  # There will be one artificial ctor function for the state vars

        addition = get_ssa_of_type(f, Binary)[0]
        assert addition.type == BinaryType.ADDITION
        assert isinstance(addition.variable_right, Constant)
        a_0 = addition.variable_left
        assert isinstance(a_0, StateIRVariable)
        assert a_0.name == "a"

        assignment = get_ssa_of_type(f, Assignment)[0]
        a_1 = assignment.lvalue
        assert isinstance(a_1, StateIRVariable)
        assert a_1.index == a_0.index + 1
        assert a_1.name == "a"
        assert assignment.rvalue == addition.lvalue

        assert a_0.non_ssa_version == a_1.non_ssa_version
        assert isinstance(a_0.non_ssa_version, StateVariable)

        # No conditional/other function interaction so no phis
        assert len(get_ssa_of_type(f, Phi)) == 0


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_initial_version_exists_for_state_variables_function_assign():
    """
    In solidity you can write statements such as
    uint a = a + 1, this test ensures that can be handled for local variables.
    """
    # TODO (hbrodin): Could be a detector that a is not used in f
    src = """
    contract C {
        uint a = f();

        function f() internal returns(uint) {
            return a;
        }
    }
    """
    with slither_from_source(src) as slither:
        verify_properties_hold(slither)
        c = slither.contracts[0]
        f, ctor = c.functions
        if f.is_constructor_variables:
            f, ctor = ctor, f

        # ctor should have a single call to f that assigns to a
        # temporary variable, that is then assigned to a

        call = get_ssa_of_type(ctor, InternalCall)[0]
        assert call.function == f
        assign = get_ssa_of_type(ctor, Assignment)[0]
        assert assign.rvalue == call.lvalue
        assert isinstance(assign.lvalue, StateIRVariable)
        assert assign.lvalue.name == "a"

        # f should have a phi node on entry of a0, a1 and should return
        # a2
        phi = get_ssa_of_type(f, Phi)[0]
        assert len(phi.rvalues) == 2
        assert assign.lvalue in phi.rvalues


@pytest.mark.skipif(
    not valid_version("0.4.0"), reason="Solidity version 0.4.0 not available on this platform"
)
def test_return_local_before_assign():
    src = """
    // this require solidity < 0.5
    // a variable can be returned before declared. Ensure it can be
    // handled by Slither.
    contract A {
    function local(bool my_bool) internal returns(uint){
        if(my_bool){
            return a_local;
        }

        uint a_local = 10;
    }
    }
    """
    with slither_from_source(src, "0.4.0") as slither:
        f = slither.contracts[0].functions[0]

        ret = get_ssa_of_type(f, Return)[0]
        assert len(ret.values) == 1
        assert ret.values[0].index == 0

        assign = get_ssa_of_type(f, Assignment)[0]
        assert assign.lvalue.index == 1
        assert assign.lvalue.non_ssa_version == ret.values[0].non_ssa_version


@pytest.mark.skipif(
    not valid_version("0.5.0"), reason="Solidity version 0.5.0 not available on this platform"
)
def test_shadow_local():
    src = """
    contract A {
     // this require solidity 0.5
    function shadowing_local() internal{
        uint local = 0;
        {
            uint local = 1;
            {
                uint local = 2;
            }
        }
    }
    }
    """
    with slither_from_source(src, "0.5.0") as slither:
        _dump_functions(slither.contracts[0])
        f = slither.contracts[0].functions[0]

        # Ensure all assignments are to a variable of index 1
        # not using the same IR var.
        assert all(map(lambda x: x.lvalue.index == 1, get_ssa_of_type(f, Assignment)))


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_multiple_named_args_returns():
    """Verifies that named arguments and return values have correct versions

    Each arg/ret have an initial version, version 0, and is written once and should
    then have version 1.
    """
    src = """
    contract A {
        function multi(uint arg1, uint arg2) internal returns (uint ret1, uint ret2) {
            arg1 = arg1 + 1;
            arg2 = arg2 + 2;
            ret1 = arg1 + 3;
            ret2 = arg2 + 4;
        }
    }"""
    with slither_from_source(src) as slither:
        verify_properties_hold(slither)
        f = slither.contracts[0].functions[0]

        # Ensure all LocalIRVariables (not TemporaryVariables) have index 1
        assert all(
            map(
                lambda x: x.lvalue.index == 1 or not isinstance(x.lvalue, LocalIRVariable),
                get_ssa_of_type(f, OperationWithLValue),
            )
        )


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_issue_468():
    """
    Ensure issue 468 is corrected as per
    https://github.com/crytic/slither/issues/468#issuecomment-620974151
    The one difference is that we allow the phi-function at entry of f to
    hold exit state which contains init state and state from branch, which
    is a bit redundant. This could be further simplified.
    """
    source = """
    contract State {
    int state = 0;
    function f(int a) public returns (int) {
        // phi-node here for state
        if (a < 1) {
            state += 1;
        }
        // phi-node here for state
        return state;
    }
    }
    """
    with slither_from_source(source) as slither:
        c = slither.get_contract_from_name("State")[0]
        f = [x for x in c.functions if x.name == "f"][0]

        # Check that there is an entry point phi values for each later value
        # plus one additional which is the initial value
        entry_ssa = f.entry_point.irs_ssa
        assert len(entry_ssa) == 1
        phi_entry = entry_ssa[0]
        assert isinstance(phi_entry, Phi)

        # Find the second phi function
        endif_node = [x for x in f.nodes if x.type == NodeType.ENDIF][0]
        assert len(endif_node.irs_ssa) == 1
        phi_endif = endif_node.irs_ssa[0]
        assert isinstance(phi_endif, Phi)

        # Ensure second phi-function contains init-phi and one additional
        assert len(phi_endif.rvalues) == 2
        assert phi_entry.lvalue in phi_endif.rvalues

        # Find return-statement and ensure it returns the phi_endif
        return_node = [x for x in f.nodes if x.type == NodeType.RETURN][0]
        assert len(return_node.irs_ssa) == 1
        ret = return_node.irs_ssa[0]
        assert len(ret.values) == 1
        assert phi_endif.lvalue in ret.values

        # Ensure that the phi_endif (which is the end-state for function as well) is in the entry_phi
        assert phi_endif.lvalue in phi_entry.rvalues


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_issue_434():
    source = """
     contract Contract {
        int public a;
        function f() public {
            g();
            a += 1;
        }

        function e() public {
            a -= 1;
        }

        function g() public {
            e();
        }
    }
    """
    with slither_from_source(source) as slither:
        c = slither.get_contract_from_name("Contract")[0]

        e = [x for x in c.functions if x.name == "e"][0]
        f = [x for x in c.functions if x.name == "f"][0]
        g = [x for x in c.functions if x.name == "g"][0]

        # Ensure there is a phi-node at the beginning of f and e
        phi_entry_e = get_ssa_of_type(e.entry_point, Phi)[0]
        phi_entry_f = get_ssa_of_type(f.entry_point, Phi)[0]
        # But not at g
        assert len(get_ssa_of_type(g, Phi)) == 0

        # Ensure that the final states of f and e are in the entry-states
        add_f = get_filtered_ssa(
            f, lambda x: isinstance(x, Binary) and x.type == BinaryType.ADDITION
        )[0]
        sub_e = get_filtered_ssa(
            e, lambda x: isinstance(x, Binary) and x.type == BinaryType.SUBTRACTION
        )[0]
        assert add_f.lvalue in phi_entry_f.rvalues
        assert add_f.lvalue in phi_entry_e.rvalues
        assert sub_e.lvalue in phi_entry_f.rvalues
        assert sub_e.lvalue in phi_entry_e.rvalues

        # Ensure there is a phi-node after call to g
        call = get_ssa_of_type(f, InternalCall)[0]
        idx = call.node.irs_ssa.index(call)
        aftercall_phi = call.node.irs_ssa[idx + 1]
        assert isinstance(aftercall_phi, Phi)

        # Ensure that phi node ^ is used in the addition afterwards
        assert aftercall_phi.lvalue in (add_f.variable_left, add_f.variable_right)


@pytest.mark.skip(reason="Fails in current slither version. Fix in #1102.")
def test_issue_473():
    source = """
    contract Contract {
    function f() public returns (int) {
        int a = 1;
        if (a > 0) {
            a = 2;
        }
        if (a == 3) {
            a = 6;
        }
        return a;
    }
    }
    """
    with slither_from_source(source) as slither:
        c = slither.get_contract_from_name("Contract")[0]
        f = c.functions[0]

        phis = get_ssa_of_type(f, Phi)
        return_value = get_ssa_of_type(f, Return)[0]

        # There shall be two phi functions
        assert len(phis) == 2
        first_phi = phis[0]
        second_phi = phis[1]

        # The second phi is the one being returned, if it's the first swap them (iteration order)
        if first_phi.lvalue in return_value.values:
            first_phi, second_phi = second_phi, first_phi

        # First phi is for [a=1 or a=2]
        assert len(first_phi.rvalues) == 2

        # second is for [a=6 or first phi]
        assert first_phi.lvalue in second_phi.rvalues
        assert len(second_phi.rvalues) == 2

        # return is for second phi
        assert len(return_value.values) == 1
        assert second_phi.lvalue in return_value.values
