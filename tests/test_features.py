import inspect
from pathlib import Path

from crytic_compile import CryticCompile
from crytic_compile.platform.solc_standard_json import SolcStandardJson
from solc_select import solc_select

from slither import Slither
from slither.core.variables.state_variable import StateVariable
from slither.detectors import all_detectors
from slither.detectors.abstract_detector import AbstractDetector
from slither.slithir.operations import InternalCall, LibraryCall
from slither.utils.arithmetic import unchecked_arithemtic_usage


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
    solc_select.switch_global_version("0.8.0", always_install=True)
    standard_json = SolcStandardJson()
    standard_json.add_source_file("./tests/collisions/a.sol")
    standard_json.add_source_file("./tests/collisions/b.sol")

    compilation = CryticCompile(standard_json)
    slither = Slither(compilation)

    _run_all_detectors(slither)


def test_cycle() -> None:
    solc_select.switch_global_version("0.8.0", always_install=True)
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


def test_contract_comments() -> None:
    comments = " @title Test Contract\n @dev Test comment"

    solc_select.switch_global_version("0.8.10", always_install=True)
    slither = Slither("./tests/custom_comments/contract_comment.sol")
    compilation_unit = slither.compilation_units[0]
    contract = compilation_unit.get_contract_from_name("A")[0]

    assert contract.comments == comments

    # Old solc versions have a different parsing of comments
    # the initial space (after *) is also not kept on every line
    comments = "@title Test Contract\n@dev Test comment"
    solc_select.switch_global_version("0.5.16", always_install=True)
    slither = Slither("./tests/custom_comments/contract_comment.sol")
    compilation_unit = slither.compilation_units[0]
    contract = compilation_unit.get_contract_from_name("A")[0]

    assert contract.comments == comments

    # Test with legacy AST
    comments = "@title Test Contract\n@dev Test comment"
    solc_select.switch_global_version("0.5.16", always_install=True)
    slither = Slither("./tests/custom_comments/contract_comment.sol", solc_force_legacy_json=True)
    compilation_unit = slither.compilation_units[0]
    contract = compilation_unit.get_contract_from_name("A")[0]

    assert contract.comments == comments


def test_using_for_top_level_same_name() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither("./tests/ast-parsing/using-for-3-0.8.0.sol")
    contract_c = slither.get_contract_from_name("C")[0]
    libCall = contract_c.get_function_from_full_name("libCall(uint256)")
    for ir in libCall.all_slithir_operations():
        if isinstance(ir, LibraryCall) and ir.destination == "Lib" and ir.function_name == "a":
            return
    assert False


def test_using_for_top_level_implicit_conversion() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither("./tests/ast-parsing/using-for-4-0.8.0.sol")
    contract_c = slither.get_contract_from_name("C")[0]
    libCall = contract_c.get_function_from_full_name("libCall(uint16)")
    for ir in libCall.all_slithir_operations():
        if isinstance(ir, LibraryCall) and ir.destination == "Lib" and ir.function_name == "f":
            return
    assert False


def test_using_for_alias_top_level() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither("./tests/ast-parsing/using-for-alias-top-level-0.8.0.sol")
    contract_c = slither.get_contract_from_name("C")[0]
    libCall = contract_c.get_function_from_full_name("libCall(uint256)")
    ok = False
    for ir in libCall.all_slithir_operations():
        if isinstance(ir, LibraryCall) and ir.destination == "Lib" and ir.function_name == "b":
            ok = True
    if not ok:
        assert False
    topLevelCall = contract_c.get_function_from_full_name("topLevel(uint256)")
    for ir in topLevelCall.all_slithir_operations():
        if isinstance(ir, InternalCall) and ir.function_name == "a":
            return
    assert False


def test_using_for_alias_contract() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither("./tests/ast-parsing/using-for-alias-contract-0.8.0.sol")
    contract_c = slither.get_contract_from_name("C")[0]
    libCall = contract_c.get_function_from_full_name("libCall(uint256)")
    ok = False
    for ir in libCall.all_slithir_operations():
        if isinstance(ir, LibraryCall) and ir.destination == "Lib" and ir.function_name == "b":
            ok = True
    if not ok:
        assert False
    topLevelCall = contract_c.get_function_from_full_name("topLevel(uint256)")
    for ir in topLevelCall.all_slithir_operations():
        if isinstance(ir, InternalCall) and ir.function_name == "a":
            return
    assert False


def test_using_for_in_library() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither("./tests/ast-parsing/using-for-in-library-0.8.0.sol")
    contract_c = slither.get_contract_from_name("A")[0]
    libCall = contract_c.get_function_from_full_name("a(uint256)")
    for ir in libCall.all_slithir_operations():
        if isinstance(ir, LibraryCall) and ir.destination == "B" and ir.function_name == "b":
            return
    assert False


def test_private_variable() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither("./tests/lookup/private_variable.sol")
    contract_c = slither.get_contract_from_name("C")[0]
    f = contract_c.functions[0]
    var_read = f.variables_read[0]
    assert isinstance(var_read, StateVariable)
    assert str(var_read.contract) == "B"


def test_arithmetic_usage() -> None:
    solc_select.switch_global_version("0.8.15", always_install=True)
    slither = Slither("./tests/arithmetic_usage/test.sol")

    assert {
        f.source_mapping.content_hash for f in unchecked_arithemtic_usage(slither.contracts[0])
    } == {"2b4bc73cf59d486dd9043e840b5028b679354dd9", "e4ecd4d0fda7e762d29aceb8425f2c5d4d0bf962"}


def test_using_for_global_collision() -> None:
    solc_select.switch_global_version("0.8.18", always_install=True)
    standard_json = SolcStandardJson()
    for source_file in Path("./tests/using-for-global-collision").rglob("*.sol"):
        standard_json.add_source_file(Path(source_file).as_posix())
    compilation = CryticCompile(standard_json)
    sl = Slither(compilation)
    _run_all_detectors(sl)


def test_abstract_contract() -> None:
    solc_select.switch_global_version("0.8.0", always_install=True)
    slither = Slither("./tests/function_features/abstract.sol")
    assert not slither.contracts[0].is_fully_implemented

    solc_select.switch_global_version("0.5.0", always_install=True)
    slither = Slither("./tests/function_features/implicit_abstract.sol")
    assert not slither.contracts[0].is_fully_implemented

    slither = Slither(
        "./tests/function_features/implicit_abstract.sol", solc_force_legacy_json=True
    )
    assert not slither.contracts[0].is_fully_implemented
