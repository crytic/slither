from pathlib import Path

from slither import Slither
from slither.slithir.convert import reorder_arguments
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.new_structure import NewStructure
from slither.slithir.variables.constant import Constant

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
ARG_REORDER_TEST_ROOT = Path(TEST_DATA_DIR, "argument_reorder")


def test_struct_constructor_reorder(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(
        Path(ARG_REORDER_TEST_ROOT, "test_struct_constructor.sol").as_posix(), solc=solc_path
    )

    operations = slither.contracts[0].functions[0].slithir_operations
    constructor_calls = [x for x in operations if isinstance(x, NewStructure)]
    assert len(constructor_calls) == 2

    # Arguments to first call are 2, 3
    assert (
        isinstance(constructor_calls[0].arguments[0], Constant)
        and constructor_calls[0].arguments[0].value == 2
    )
    assert (
        isinstance(constructor_calls[0].arguments[1], Constant)
        and constructor_calls[0].arguments[1].value == 3
    )

    # Arguments to second call are 5, 4 (note the reversed order)
    assert (
        isinstance(constructor_calls[1].arguments[0], Constant)
        and constructor_calls[1].arguments[0].value == 5
    )
    assert (
        isinstance(constructor_calls[1].arguments[1], Constant)
        and constructor_calls[1].arguments[1].value == 4
    )


def test_internal_call_reorder(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(
        Path(ARG_REORDER_TEST_ROOT, "test_internal_call_reorder.sol").as_posix(), solc=solc_path
    )

    operations = slither.contracts[0].functions[1].slithir_operations
    internal_calls = [x for x in operations if isinstance(x, InternalCall)]
    assert len(internal_calls) == 1

    # Arguments to call are 3, true, 5
    assert (
        isinstance(internal_calls[0].arguments[0], Constant)
        and internal_calls[0].arguments[0].value == 3
    )
    assert (
        isinstance(internal_calls[0].arguments[1], Constant)
        and internal_calls[0].arguments[1].value is True
    )
    assert (
        isinstance(internal_calls[0].arguments[2], Constant)
        and internal_calls[0].arguments[2].value == 5
    )


def test_overridden_function_reorder(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(
        Path(ARG_REORDER_TEST_ROOT, "test_overridden_function.sol").as_posix(), solc=solc_path
    )

    operations = slither.contracts[0].functions[1].slithir_operations
    internal_calls = [x for x in operations if isinstance(x, InternalCall)]
    assert len(internal_calls) == 1

    assert (
        isinstance(internal_calls[0].arguments[0], Constant)
        and internal_calls[0].arguments[0].value == 23
    )
    assert (
        isinstance(internal_calls[0].arguments[1], Constant)
        and internal_calls[0].arguments[1].value == 36
    )
    assert (
        isinstance(internal_calls[0].arguments[2], Constant)
        and internal_calls[0].arguments[2].value == 34
    )

    operations = slither.contracts[1].functions[1].slithir_operations
    internal_calls = [x for x in operations if isinstance(x, InternalCall)]
    assert len(internal_calls) == 1

    assert (
        isinstance(internal_calls[0].arguments[0], Constant)
        and internal_calls[0].arguments[0].value == 23
    )
    assert (
        isinstance(internal_calls[0].arguments[1], Constant)
        and internal_calls[0].arguments[1].value == 36
    )
    assert (
        isinstance(internal_calls[0].arguments[2], Constant)
        and internal_calls[0].arguments[2].value == 34
    )


def test_reorder_arguments_mismatched_decl_lengths() -> None:
    """Regression test for https://github.com/crytic/slither/issues/2217

    reorder_arguments should not crash when decl_names contains entries
    whose length doesn't match the call argument count. This can happen
    when Slither misresolves a struct to a same-named struct with a
    different number of fields.
    """
    args = ["a_val", "b_val", "c_val"]
    call_names = ["a", "b", "c"]

    # All decl_names entries have a mismatched length — args returned as-is
    decl_names_all_wrong = [["x"], ["p", "q"]]
    result = reorder_arguments(args, call_names, decl_names_all_wrong)
    assert result == args

    # One matching entry among mismatched ones — reordering still works
    decl_names_mixed = [["x"], ["c", "a", "b"], ["p", "q"]]
    result = reorder_arguments(args, call_names, decl_names_mixed)
    assert result == ["c_val", "a_val", "b_val"]

    # Empty decl_names — args returned as-is
    result = reorder_arguments(args, call_names, [])
    assert result == args


def test_same_name_struct_no_crash(solc_binary_path) -> None:
    """Regression test for https://github.com/crytic/slither/issues/2217

    Two contracts define structs with the same name but different field
    counts. Slither must not crash when processing named struct constructor
    arguments.
    """
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(
        Path(ARG_REORDER_TEST_ROOT, "test_same_name_structs.sol").as_posix(), solc=solc_path
    )

    # Verify both contracts were parsed without crashing
    contract_names = [c.name for c in slither.contracts]
    assert "A" in contract_names
    assert "B" in contract_names

    # Verify struct constructors were found in both contracts
    for contract in slither.contracts:
        test_func = next(f for f in contract.functions if f.name == "test")
        constructor_calls = [
            op for op in test_func.slithir_operations if isinstance(op, NewStructure)
        ]
        assert len(constructor_calls) >= 1
