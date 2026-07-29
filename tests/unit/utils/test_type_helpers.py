from pathlib import Path
from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_function_id_rec_structure(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "type_helpers.sol").as_posix(), solc=solc_path)
    for compilation_unit in slither.compilation_units:
        for function in compilation_unit.functions:
            assert function.solidity_signature


def test_solidity_signature_repeated_struct_field_types(solc_binary_path) -> None:
    """A type used by two fields of the same struct must be converted for both of them."""
    solc_path = solc_binary_path("0.8.20")
    slither = Slither(
        Path(TEST_DATA_DIR, "type_helpers_repeated_fields.sol").as_posix(), solc=solc_path
    )
    contract = slither.get_contract_from_name("B")[0]
    signatures = {f.name: f.solidity_signature for f in contract.functions_entry_points}

    assert signatures["fAlias"] == "fAlias((uint256,uint256))"
    assert signatures["fEnum"] == "fEnum((uint8,uint8))"
    assert signatures["fContract"] == "fContract((address,address))"
