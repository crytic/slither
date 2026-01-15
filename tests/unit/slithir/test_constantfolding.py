from pathlib import Path

from slither import Slither
from slither.printers.guidance.echidna import _extract_constants, ConstantValue

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_enum_max_min(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.19")
    slither = Slither(Path(TEST_DATA_DIR, "constantfolding.sol").as_posix(), solc=solc_path)

    contracts = slither.get_contract_from_name("A")

    constants = _extract_constants(contracts)[0]["A"]["use()"]

    assert set(constants) == {
        ConstantValue(value="2", type="uint256"),
        ConstantValue(value="10", type="uint256"),
        ConstantValue(value="100", type="uint256"),
        ConstantValue(value="4294967295", type="uint32"),
    }
