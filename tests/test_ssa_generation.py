import pathlib
import tempfile
from collections import defaultdict
from typing import Union

from slither import Slither
from slither.core.cfg.node import Node
from slither.core.declarations import Function
from slither.slithir.operations import OperationWithLValue, Phi
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
    ssa_lvalue_names = set()
    ssa_rvalues = set()
    lvalue_assignments = {}

    def get_name(ssa_var: Union[TemporaryVariableSSA, SlithIRVariable]) -> str:
        if isinstance(ssa_var, TemporaryVariableSSA):
            return ssa_var.name
        return ssa_var.ssa_name

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
                print(ssa)
                # 1
                assert ssa.lvalue not in ssa_lvalues
                ssa_lvalues.add(ssa.lvalue)

                # 1
                assert get_name(ssa.lvalue) not in ssa_lvalue_names
                ssa_lvalue_names.add(get_name(ssa.lvalue))

            for rvalue in filter(lambda x: not isinstance(x, Constant), ssa.read):
                ssa_rvalues.add(rvalue)

    # 2
    for rvalue in ssa_rvalues:
        assert get_name(rvalue) in ssa_lvalue_names
        assert rvalue in ssa_lvalues

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

    for node in f.nodes:
        if node.dominance_frontier:
            for df in node.dominance_frontier:
                for ssa in node.irs_ssa:
                    if isinstance(ssa, OperationWithLValue):
                        if is_used_later(node, ssa.lvalue):
                            assert have_phi_for_var(df, ssa.lvalue)


def verify_properties_hold(source_code: str):
    # TODO (hbrodin): CryticCompile won't compile files unless dir is specified as cwd. Not sure why.
    with tempfile.NamedTemporaryFile(suffix=".sol", mode="w", dir=pathlib.Path().cwd()) as f:
        f.write(source_code)
        f.flush()

        slither = Slither(f.name)

        for cu in slither.compilation_units:
            for func in cu.functions_and_modifiers:
                phi_values_inserted(func)
                ssa_basic_properties(func)
                ssa_phi_node_properties(func)
                dominance_properties(func)


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
