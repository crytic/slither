from pathlib import Path
from slither import Slither


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_local_alias(solc_binary_path) -> None:

    solc_path = solc_binary_path("0.8.18")
    slither = Slither(
        Path(TEST_DATA_DIR, "variable_read_write_storage_pointer/local_alias.sol").as_posix(),
        solc=solc_path,
    )

    contract = slither.get_contract_from_name("Test")[0]

    test = contract.get_function_from_full_name("test()")

    s0 = contract.get_state_variable_from_name("s0")
    s1 = contract.get_state_variable_from_name("s1")

    assert set(test.state_variables_written) == {s0, s1}


def test_parameter_no_library(solc_binary_path) -> None:

    solc_path = solc_binary_path("0.8.18")
    slither = Slither(
        Path(TEST_DATA_DIR, "variable_read_write_storage_pointer/without_library.sol").as_posix(),
        solc=solc_path,
    )

    contract = slither.get_contract_from_name("MinterRole")[0]

    print(contract.available_functions_as_dict())
    add = contract.get_function_from_full_name("add(MinterRole.Role,address)")
    has = contract.get_function_from_full_name("has(MinterRole.Role,address)")

    minter = contract.get_state_variable_from_name("_minters")

    assert set(add.state_variables_written) == {minter}
    assert set(add.state_variables_read) == {minter}
    assert set(has.state_variables_written) == set()
    assert set(has.state_variables_read) == {minter}
