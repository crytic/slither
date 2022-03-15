import pathlib
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from typing import Union

from slither import Slither
from slither.core.cfg.node import Node
from slither.core.declarations import Function, Contract
from slither.slithir.operations import OperationWithLValue, Phi, Assignment, HighLevelCall
from slither.slithir.utils.ssa import is_used_later
from slither.slithir.variables import Constant, TemporaryVariableSSA
from slither.slithir.variables.variable import SlithIRVariable


def ssa_basic_properties(function: Function):
    """Verifies that basic properties of ssa holds

    1. Every name is defined only once
    2. Every r-value is at least defined at some point
    3. The number of ssa defs is >= the number of assignments to var
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
    print(f"---- {f} ----")
    for n in f.nodes:
        print(n)
        for ir in n.irs_ssa:
            print(f"\t{ir}")
    print("")

def _dump_functions(c: Contract):
    """Helper function to print functions and modifiers of a contract"""
    for f in c.functions_and_modifiers:
        _dump_function(f)


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
        print(funcs)
        direct_set = funcs["direct_set(uint256)"]
        # Skip entry point and go straight to assignment ir
        assign1 = direct_set.nodes[1].irs_ssa[0]
        assert isinstance(assign1, Assignment)

        direct_set_plus_one = funcs["direct_set_plus_one(uint256)"]
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

        entry_phi = [x for x in f.entry_point.irs_ssa if isinstance(x, Phi) and x.lvalue.non_ssa_version == var_a][0]
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
        after_call_phi = n.irs_ssa[n.irs_ssa.index(call_node)+1]
        # The two sources for this phi node is
        # 1. my_var_A = i;
        # 2. my_var_A = 3;
        assert isinstance(after_call_phi, Phi)
        assert len(after_call_phi.rvalues) == 2
