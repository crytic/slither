import pathlib
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from typing import Union, List

from slither import Slither
from slither.core.cfg.node import Node, NodeType
from slither.core.declarations import Function, Contract
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
from slither.slithir.variables import Constant


def ssa_basic_properties(function: Function):
    """Verifies that basic properties of ssa holds

    1. Every name is defined only once
    2. Every r-value is at least defined at some point
    3. The number of ssa defs is >= the number of assignments to var
    4. Function parameters SSA are stored in function.parameters_ssa
       - if function parameter is_storage it refers to a fake variable
    5. Function returns SSA are stored in function.returns_ssa
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

            for rvalue in filter(lambda x: not isinstance(x, Constant), ssa.read):
                ssa_rvalues.add(rvalue)

    # 2
    # Each var can have one non-defined value, the value initially held. Typically,
    # var_0, i_0, state_0 or similar.
    undef_vars = set()
    for rvalue in ssa_rvalues:
        if rvalue not in ssa_lvalues:
            assert rvalue.non_ssa_version not in undef_vars
            undef_vars.add(rvalue.non_ssa_version)

    # 3
    ssa_defs = defaultdict(int)
    for v in ssa_lvalues:
        ssa_defs[v.name] += 1

    for (k, n) in lvalue_assignments.items():
        assert ssa_defs[k] >= n


    # Helper 4/5
    def check_property_4_and_5(vars, ssavars):
        for var in filter(lambda x: x.name, vars):
            ssa_vars = [x for x in ssavars if x.non_ssa_version == var]
            assert len(ssa_vars) == 1
            ssa_var = ssa_vars[0]
            assert var.is_storage == ssa_var.is_storage
            if ssa_var.is_storage:
                assert len(ssa_var.refers_to) == 1
                assert ssa_var.refers_to[0].location == "reference_to_storage"

    # 4
    check_property_4_and_5(function.parameters, function.parameters_ssa)

    # 5
    check_property_4_and_5(function.returns, function.return_values_ssa)


def ssa_phi_node_properties(f: Function):
    """Every phi-function should have as many args as predecessors"""
    for node in f.nodes:
        for ssa in node.irs_ssa:
            if isinstance(ssa, Phi):
                n = len(ssa.read)
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
def slither_from_source(source_code: str):
    # TODO (hbrodin): CryticCompile won't compile files unless dir is specified as cwd. Not sure why.
    with tempfile.NamedTemporaryFile(suffix=".sol", mode="w", dir=pathlib.Path().cwd()) as f:
        f.write(source_code)
        f.flush()

        yield Slither(f.name)


def verify_properties_hold(source_code: str):
    with slither_from_source(source_code) as slither:
        for cu in slither.compilation_units:
            for func in cu.functions_and_modifiers:
                phi_values_inserted(func)
                ssa_basic_properties(func)
                ssa_phi_node_properties(func)
                dominance_properties(func)


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


def test_issue_468():
    """ "
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
