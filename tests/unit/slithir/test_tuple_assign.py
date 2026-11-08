from pathlib import Path

from slither import Slither
from slither.slithir.operations import Assignment, Binary
from slither.slithir.operations.unpack import Unpack
from slither.slithir.variables import TemporaryVariable

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "tuple_assign"


def test_tuple_order(solc_binary_path) -> None:
    """Test that the correct tuple components are projected when some components are left empty."""
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(TEST_DATA_DIR, "test_tuple_assign.sol").as_posix(), solc=solc_path)
    fn = slither.get_contract_from_name("TestEmptyComponent")[0].get_function_from_canonical_name(
        "TestEmptyComponent.test()"
    )
    unpacks = [ir for ir in fn.slithir_operations if isinstance(ir, Unpack)]
    assert unpacks[0].index == 0
    assert unpacks[1].index == 2
    assert unpacks[2].index == 3


def test_tuple_reassign(solc_binary_path) -> None:
    """Test that tuple component indexes are not reused across assignments"""
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(TEST_DATA_DIR, "test_tuple_assign.sol").as_posix(), solc=solc_path)
    fn = slither.get_contract_from_name("TestTupleReassign")[0].get_function_from_canonical_name(
        "TestTupleReassign.test()"
    )
    unpacks = [ir for ir in fn.slithir_operations if isinstance(ir, Unpack)]
    assert len(unpacks) == 5
    assert unpacks[3].index == 0
    assert unpacks[4].index == 1


def test_tuple_evaluation_order(solc_binary_path) -> None:
    """Test that tuple components are read before later components mutate them."""
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(Path(TEST_DATA_DIR, "test_tuple_assign.sol").as_posix(), solc=solc_path)
    fn = slither.get_contract_from_name("TestTupleEvaluationOrder")[
        0
    ].get_function_from_canonical_name("TestTupleEvaluationOrder.test()")
    irs = fn.slithir_operations

    assignment_a = next(ir for ir in irs if isinstance(ir, Assignment) and ir.lvalue.name == "a")
    assert isinstance(assignment_a.rvalue, TemporaryVariable)

    capture_index = next(
        index
        for index, ir in enumerate(irs)
        if isinstance(ir, Assignment) and ir.lvalue is assignment_a.rvalue
    )
    increment_index = next(
        index
        for index, ir in enumerate(irs)
        if isinstance(ir, Binary) and ir.lvalue.name == "index"
    )
    assert capture_index < increment_index
