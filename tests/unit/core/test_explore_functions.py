"""
Tests for `Function._explore_functions` and its dependent methods:
- all_variables_read
- all_variables_written
- all_state_variables_read
- all_state_variables_written

These tests verify that the recursive function traversal correctly discovers
all variables across call chains, cycles, diamond patterns, modifiers, and
library calls.
"""

from pathlib import Path

from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
EXPLORE_FUNCS_TEST_ROOT = Path(TEST_DATA_DIR, "explore_functions")


def test_simple_chain(solc_binary_path):
    """Test that variables from a call chain A -> B -> C are all discovered."""
    solc_path = solc_binary_path("0.8.19")
    file = Path(EXPLORE_FUNCS_TEST_ROOT, "test_call_graph.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    contract = slither.get_contract_from_name("TestCallGraph")[0]

    chain_a = contract.get_function_from_signature("chainA()")
    assert chain_a is not None

    # chainA -> chainB -> chainC should discover stateA, stateB, stateC
    all_written = chain_a.all_state_variables_written()
    written_names = {v.name for v in all_written}

    assert "stateA" in written_names
    assert "stateB" in written_names
    assert "stateC" in written_names


def test_cycle_two_functions(solc_binary_path):
    """Test that cycles don't cause infinite loops and both functions' vars are found."""
    solc_path = solc_binary_path("0.8.19")
    file = Path(EXPLORE_FUNCS_TEST_ROOT, "test_call_graph.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    contract = slither.get_contract_from_name("TestCallGraph")[0]

    cycle_a = contract.get_function_from_signature("cycleA()")
    assert cycle_a is not None

    # cycleA -> cycleB should find both stateA and stateB
    all_written = cycle_a.all_state_variables_written()
    written_names = {v.name for v in all_written}

    assert "stateA" in written_names
    assert "stateB" in written_names


def test_diamond_pattern(solc_binary_path):
    """Test diamond pattern: top -> left & right -> bottom."""
    solc_path = solc_binary_path("0.8.19")
    file = Path(EXPLORE_FUNCS_TEST_ROOT, "test_call_graph.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    contract = slither.get_contract_from_name("TestCallGraph")[0]

    diamond_top = contract.get_function_from_signature("diamondTop()")
    assert diamond_top is not None

    # diamondTop -> diamondLeft & diamondRight -> diamondBottom
    # Should find stateTop, stateLeft, stateRight, stateBottom
    all_written = diamond_top.all_state_variables_written()
    written_names = {v.name for v in all_written}

    assert "stateTop" in written_names
    assert "stateLeft" in written_names
    assert "stateRight" in written_names
    assert "stateBottom" in written_names

    # Verify bottom appears exactly once (deduplicated)
    bottom_count = sum(1 for v in all_written if v.name == "stateBottom")
    assert bottom_count == 1


def test_modifier_traversal(solc_binary_path):
    """Test that modifier's state variables are included."""
    solc_path = solc_binary_path("0.8.19")
    file = Path(EXPLORE_FUNCS_TEST_ROOT, "test_call_graph.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    contract = slither.get_contract_from_name("TestCallGraph")[0]

    with_modifier = contract.get_function_from_signature("withModifier()")
    assert with_modifier is not None

    # withModifier uses testModifier which writes stateModifier
    all_written = with_modifier.all_state_variables_written()
    written_names = {v.name for v in all_written}

    assert "stateA" in written_names  # From function body
    assert "stateModifier" in written_names  # From modifier


def test_library_call_traversal(solc_binary_path):
    """Test that library functions are traversed."""
    solc_path = solc_binary_path("0.8.19")
    file = Path(EXPLORE_FUNCS_TEST_ROOT, "test_call_graph.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    contract = slither.get_contract_from_name("TestCallGraph")[0]

    with_lib = contract.get_function_from_signature("withLibraryCall(uint256)")
    assert with_lib is not None

    # withLibraryCall calls TestLib.libFunc which reads LIB_CONST
    # The function writes stateLib
    all_written = with_lib.all_state_variables_written()
    written_names = {v.name for v in all_written}

    assert "stateLib" in written_names


def test_standalone_no_calls(solc_binary_path):
    """Test that standalone function returns only its own variables."""
    solc_path = solc_binary_path("0.8.19")
    file = Path(EXPLORE_FUNCS_TEST_ROOT, "test_call_graph.sol").as_posix()
    slither = Slither(file, solc=solc_path)
    contract = slither.get_contract_from_name("TestCallGraph")[0]

    standalone = contract.get_function_from_signature("standalone()")
    assert standalone is not None

    # standalone() only writes stateStandalone
    all_written = standalone.all_state_variables_written()
    written_names = {v.name for v in all_written}

    assert "stateStandalone" in written_names
    # Should not include variables from other functions
    assert "stateA" not in written_names
    assert "stateB" not in written_names
    assert "stateTop" not in written_names
