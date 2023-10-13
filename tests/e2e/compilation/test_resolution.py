from pathlib import Path
import pytest

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson

from slither import Slither

from tests.utils import _run_all_detectors


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

hardhat_available = Path(TEST_DATA_DIR, "test_node_modules/node_modules/hardhat").exists()


@pytest.mark.skipif(not hardhat_available, reason="requires Hardhat and project setup")
def test_node_modules() -> None:
    # hardhat must have been installed in tests/test_node_modules
    # For the CI its done through the github action config

    slither = Slither(Path(TEST_DATA_DIR, "test_node_modules").as_posix())
    _run_all_detectors(slither)


def test_contract_name_collision(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    standard_json.add_source_file(
        Path(TEST_DATA_DIR, "test_contract_name_collisions", "a.sol").as_posix()
    )
    standard_json.add_source_file(
        Path(TEST_DATA_DIR, "test_contract_name_collisions", "b.sol").as_posix()
    )

    compilation = CryticCompile(standard_json, solc=solc_path)
    slither = Slither(compilation)

    _run_all_detectors(slither)


def test_cycle(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "test_cyclic_import", "a.sol").as_posix(), solc=solc_path)
    _run_all_detectors(slither)


def test_contract_function_parameter(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    standard_json = SolcStandardJson()
    standard_json.add_source_file(
        Path(TEST_DATA_DIR, "test_contract_data", "test_contract_data.sol").as_posix()
    )
    compilation = CryticCompile(standard_json, solc=solc_path)
    slither = Slither(compilation)
    contract = slither.contracts[0]
    function = contract.functions[0]
    parameters = function.parameters

    assert (parameters[0].name == 'param1')
    assert (parameters[1].name == '')
    assert (parameters[2].name == 'param3')
