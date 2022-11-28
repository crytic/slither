import inspect

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from solc_select import solc_select

from slither import Slither
from slither.detectors import all_detectors
from slither.detectors.abstract_detector import AbstractDetector


def _run_all_detectors(slither: Slither):
    detectors = [getattr(all_detectors, name) for name in dir(all_detectors)]
    detectors = [d for d in detectors if inspect.isclass(d) and issubclass(d, AbstractDetector)]

    for detector in detectors:
        slither.register_detector(detector)

    slither.run_detectors()


def test_node():
    # hardhat must have been installed in tests/test_node_modules
    # For the CI its done through the github action config

    slither = Slither("./tests/test_node_modules")
    _run_all_detectors(slither)


def test_collision():

    standard_json = SolcStandardJson()
    standard_json.add_source_file("./tests/collisions/a.sol")
    standard_json.add_source_file("./tests/collisions/b.sol")

    compilation = CryticCompile(standard_json)
    slither = Slither(compilation)

    _run_all_detectors(slither)


def test_cycle():
    slither = Slither("./tests/test_cyclic_import/a.sol")
    _run_all_detectors(slither)


def test_funcion_id_rec_structure():
    solc_select.switch_global_version("0.8.0", always_install=True)
    slither = Slither("./tests/function_ids/rec_struct-0.8.sol")
    for compilation_unit in slither.compilation_units:
        for function in compilation_unit.functions:
            assert function.solidity_signature
