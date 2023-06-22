from pathlib import Path
from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_function_id_rec_structure(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "type_helpers.sol").as_posix(), solc=solc_path)
    for compilation_unit in slither.compilation_units:
        for function in compilation_unit.functions:
            assert function.solidity_signature
