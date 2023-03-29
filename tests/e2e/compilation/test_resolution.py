from pathlib import Path
import pytest

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from solc_select import solc_select

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


def test_contract_name_collisions() -> None:
    solc_select.switch_global_version("0.8.0", always_install=True)
    standard_json = SolcStandardJson()
    standard_json.add_source_file(
        Path(TEST_DATA_DIR, "test_contract_name_collisions", "a.sol").as_posix()
    )
    standard_json.add_source_file(
        Path(TEST_DATA_DIR, "test_contract_name_collisions", "b.sol").as_posix()
    )

    compilation = CryticCompile(standard_json)
    slither = Slither(compilation)

    _run_all_detectors(slither)


def test_cycle() -> None:
    solc_select.switch_global_version("0.8.0", always_install=True)
    slither = Slither(Path(TEST_DATA_DIR, "test_cyclic_import", "a.sol").as_posix())
    _run_all_detectors(slither)
