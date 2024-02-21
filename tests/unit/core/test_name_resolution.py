from pathlib import Path

from slither import Slither


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
NAME_RESOLUTION_TEST_ROOT = Path(TEST_DATA_DIR, "name_resolution")


def _sort_references_lines(refs: list) -> list:
    return sorted([ref.lines[0] for ref in refs])


def test_name_resolution_compact(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(
        Path(NAME_RESOLUTION_TEST_ROOT, "shadowing_compact.sol").as_posix(), solc=solc_path
    )
    contract = slither.get_contract_from_name("B")[0]
    x = contract.get_state_variable_from_name("x")
    assert _sort_references_lines(x.references) == [5]


def test_name_resolution_legacy_post_0_5_0(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.5.0")
    slither = Slither(
        Path(NAME_RESOLUTION_TEST_ROOT, "shadowing_legacy_post_0_5_0.sol").as_posix(),
        solc=solc_path,
    )
    contract = slither.get_contract_from_name("B")[0]
    x = contract.get_state_variable_from_name("x")
    assert _sort_references_lines(x.references) == [5]


def test_name_resolution_legacy_pre_0_5_0(solc_binary_path) -> None:
    solc_path = solc_binary_path("0.4.12")
    slither = Slither(
        Path(NAME_RESOLUTION_TEST_ROOT, "shadowing_legacy_pre_0_5_0.sol").as_posix(),
        solc=solc_path,
        force_legacy=True,
    )
    contract = slither.get_contract_from_name("B")[0]
    function = contract.get_function_from_signature("a()")
    x = function.get_local_variable_from_name("x")
    assert _sort_references_lines(x.references) == [5]
