from pathlib import Path
from solc_select import solc_select
from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_function_id_rec_structure() -> None:
    solc_select.switch_global_version("0.8.0", always_install=True)
    slither = Slither(Path(TEST_DATA_DIR, "type_helpers.sol").as_posix())
    for compilation_unit in slither.compilation_units:
        for function in compilation_unit.functions:
            assert function.solidity_signature
