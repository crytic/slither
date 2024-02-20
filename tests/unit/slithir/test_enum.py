from pathlib import Path
from slither import Slither
from slither.slithir.operations import Assignment
from slither.slithir.variables import Constant

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_enum_max_min(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.19")
    slither = Slither(Path(TEST_DATA_DIR, "enum_max_min.sol").as_posix(), solc=solc_path)

    contract = slither.get_contract_from_name("D")[0]

    f = contract.get_function_from_full_name("a()")
    # TMP_1(uint256) := 2(uint256)
    assignment = f.slithir_operations[1]
    assert (
        isinstance(assignment, Assignment)
        and isinstance(assignment.rvalue, Constant)
        and assignment.rvalue.value == 2
    )

    f = contract.get_function_from_full_name("b()")
    # TMP_4(uint256) := 0(uint256)
    assignment = f.slithir_operations[1]
    assert (
        isinstance(assignment, Assignment)
        and isinstance(assignment.rvalue, Constant)
        and assignment.rvalue.value == 0
    )

    f = contract.get_function_from_full_name("c()")
    # TMP_7(uint256) := 1(uint256)
    assignment = f.slithir_operations[1]
    assert (
        isinstance(assignment, Assignment)
        and isinstance(assignment.rvalue, Constant)
        and assignment.rvalue.value == 1
    )

    f = contract.get_function_from_full_name("d()")
    # TMP_10(uint256) := 0(uint256)
    assignment = f.slithir_operations[1]
    assert (
        isinstance(assignment, Assignment)
        and isinstance(assignment.rvalue, Constant)
        and assignment.rvalue.value == 0
    )

    f = contract.get_function_from_full_name("e()")
    # TMP_13(uint256) := 0(uint256)
    assignment = f.slithir_operations[1]
    assert (
        isinstance(assignment, Assignment)
        and isinstance(assignment.rvalue, Constant)
        and assignment.rvalue.value == 0
    )

    f = contract.get_function_from_full_name("f()")
    # TMP_16(uint256) := 0(uint256)
    assignment = f.slithir_operations[1]
    assert (
        isinstance(assignment, Assignment)
        and isinstance(assignment.rvalue, Constant)
        and assignment.rvalue.value == 0
    )
