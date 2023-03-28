from pathlib import Path
from solc_select import solc_select

from slither import Slither
from slither.utils.arithmetic import unchecked_arithemtic_usage


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "arithmetic_usage"


def test_arithmetic_usage() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither(Path(TEST_DATA_DIR, "test.sol").as_posix())

    assert {
        f.source_mapping.content_hash for f in unchecked_arithemtic_usage(slither.contracts[0])
    } == {"2b4bc73cf59d486dd9043e840b5028b679354dd9", "e4ecd4d0fda7e762d29aceb8425f2c5d4d0bf962"}
