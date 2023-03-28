from pathlib import Path

from solc_select import solc_select

from slither import Slither
from slither.core.variables.state_variable import StateVariable

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
CONTRACT_DECL_TEST_ROOT = Path(TEST_DATA_DIR, "contract_declaration")


def test_abstract_contract(use_solc_version) -> None:
    solc_path = next(use_solc_version("0.8.0"))
    slither = Slither(Path(CONTRACT_DECL_TEST_ROOT, "abstract.sol").as_posix(), solc=solc_path)
    assert not slither.contracts[0].is_fully_implemented

    solc_path = next(use_solc_version("0.5.0"))
    slither = Slither(Path(CONTRACT_DECL_TEST_ROOT, "implicit_abstract.sol").as_posix(), solc=solc_path)
    assert not slither.contracts[0].is_fully_implemented

    slither = Slither(
        Path(CONTRACT_DECL_TEST_ROOT, "implicit_abstract.sol").as_posix(),
        solc_force_legacy_json=True,
        solc=solc_path
    )
    assert not slither.contracts[0].is_fully_implemented


def test_private_variable(use_solc_version) -> None:
    solc_path = next(use_solc_version("0.8.15"))
    slither = Slither(Path(CONTRACT_DECL_TEST_ROOT, "private_variable.sol").as_posix(), solc=solc_path)
    contract_c = slither.get_contract_from_name("C")[0]
    f = contract_c.functions[0]
    var_read = f.variables_read[0]
    assert isinstance(var_read, StateVariable)
    assert str(var_read.contract) == "B"
