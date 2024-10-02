from pathlib import Path


from slither import Slither
from slither.core.variables.state_variable import StateVariable

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
CONTRACT_DECL_TEST_ROOT = Path(TEST_DATA_DIR, "contract_declaration")


def test_abstract_contract(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(CONTRACT_DECL_TEST_ROOT, "abstract.sol").as_posix(), solc=solc_path)
    explicit_abstract = slither.contracts[0]
    assert not explicit_abstract.is_fully_implemented
    assert explicit_abstract.is_abstract

    solc_path = solc_binary_path("0.5.0")
    slither = Slither(
        Path(CONTRACT_DECL_TEST_ROOT, "implicit_abstract.sol").as_posix(), solc=solc_path
    )
    implicit_abstract = slither.get_contract_from_name("ImplicitAbstract")[0]
    assert not implicit_abstract.is_fully_implemented
    # This only is expected to work for newer versions of Solidity
    assert not implicit_abstract.is_abstract

    slither = Slither(
        Path(CONTRACT_DECL_TEST_ROOT, "implicit_abstract.sol").as_posix(),
        solc_force_legacy_json=True,
        solc=solc_path,
    )
    implicit_abstract = slither.get_contract_from_name("ImplicitAbstract")[0]
    assert not implicit_abstract.is_fully_implemented
    # This only is expected to work for newer versions of Solidity
    assert not implicit_abstract.is_abstract


def test_concrete_contract(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(CONTRACT_DECL_TEST_ROOT, "concrete.sol").as_posix(), solc=solc_path)
    concrete = slither.get_contract_from_name("Concrete")[0]
    assert concrete.is_fully_implemented
    assert not concrete.is_abstract

    solc_path = solc_binary_path("0.5.0")
    slither = Slither(
        Path(CONTRACT_DECL_TEST_ROOT, "concrete_old.sol").as_posix(),
        solc_force_legacy_json=True,
        solc=solc_path,
    )
    concrete_old = slither.get_contract_from_name("ConcreteOld")[0]
    assert concrete_old.is_fully_implemented
    assert not concrete_old.is_abstract


def test_private_variable(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(
        Path(CONTRACT_DECL_TEST_ROOT, "private_variable.sol").as_posix(), solc=solc_path
    )
    contract_c = slither.get_contract_from_name("C")[0]
    f = contract_c.functions[0]
    var_read = f.variables_read[0]
    assert isinstance(var_read, StateVariable)
    assert str(var_read.contract) == "B"
