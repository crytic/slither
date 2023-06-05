from pathlib import Path


from slither import Slither
from slither.core.variables.state_variable import StateVariable

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
COMPILATION_UNIT_TEST_ROOT = Path(TEST_DATA_DIR, "compilation_unit")


def test_contracts_derived(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(
        Path(COMPILATION_UNIT_TEST_ROOT, "contracts_derived.sol").as_posix(), solc=solc_path
    )
    for c in slither.contracts:
        print(c.is_test)

    names = [x.name for x in slither.contracts_derived]
    assert names == ["MyContractA", "MyContractB"]
