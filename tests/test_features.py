import inspect

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from solc_select import solc_select

from slither import Slither
from slither.detectors import all_detectors
from slither.detectors.abstract_detector import AbstractDetector


def _run_all_detectors(slither: Slither) -> None:
    detectors = [getattr(all_detectors, name) for name in dir(all_detectors)]
    detectors = [d for d in detectors if inspect.isclass(d) and issubclass(d, AbstractDetector)]

    for detector in detectors:
        slither.register_detector(detector)

    slither.run_detectors()


def test_node() -> None:
    # hardhat must have been installed in tests/test_node_modules
    # For the CI its done through the github action config

    slither = Slither("./tests/test_node_modules")
    _run_all_detectors(slither)


def test_collision() -> None:

    standard_json = SolcStandardJson()
    standard_json.add_source_file("./tests/collisions/a.sol")
    standard_json.add_source_file("./tests/collisions/b.sol")

    compilation = CryticCompile(standard_json)
    slither = Slither(compilation)

    _run_all_detectors(slither)


def test_cycle() -> None:
    slither = Slither("./tests/test_cyclic_import/a.sol")
    _run_all_detectors(slither)


def test_funcion_id_rec_structure() -> None:
    solc_select.switch_global_version("0.8.0", always_install=True)
    slither = Slither("./tests/function_ids/rec_struct-0.8.sol")
    for compilation_unit in slither.compilation_units:
        for function in compilation_unit.functions:
            assert function.solidity_signature


def test_upgradeable_comments() -> None:
    solc_select.switch_global_version("0.8.10", always_install=True)
    slither = Slither("./tests/custom_comments/upgrade.sol")
    compilation_unit = slither.compilation_units[0]
    proxy = compilation_unit.get_contract_from_name("Proxy")[0]

    assert proxy.is_upgradeable_proxy

    v0 = compilation_unit.get_contract_from_name("V0")[0]

    assert v0.is_upgradeable
    print(v0.upgradeable_version)
    assert v0.upgradeable_version == "version-0"

    v1 = compilation_unit.get_contract_from_name("V1")[0]
    assert v0.is_upgradeable
    assert v1.upgradeable_version == "version_1"
