import argparse
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest import mock

import pytest
from slither import Slither
from slither.tools.mutator.__main__ import _get_mutators, main, parse_target_selectors
from slither.tools.mutator.utils.testing_generated_mutant import run_test_cmd
from slither.tools.mutator.utils.file_handling import get_sol_file_list, backup_source_file
from slither.utils.function import get_function_id
from slither.tools.mutator.mutators.RR import RR


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"

foundry_available = shutil.which("forge") is not None
project_ready = Path(TEST_DATA_DIR, "test_source_unit/lib/forge-std").exists()


@contextmanager
def change_directory(new_dir):
    original_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(original_dir)


def test_get_mutators():

    mutators = _get_mutators(None)
    assert mutators

    mutators = _get_mutators(["ASOR"])
    assert len(mutators) == 1
    assert mutators[0].NAME == "ASOR"

    mutators = _get_mutators(["ASOR", "NotExisiting"])
    assert len(mutators) == 1


@mock.patch(
    "argparse.ArgumentParser.parse_args",
    return_value=argparse.Namespace(
        test_cmd="forge test",
        test_dir=None,
        ignore_dirs="lib,mutation_campaign",
        output_dir=None,
        timeout=None,
        solc_remaps="forge-std=./lib/forge-std",
        verbose=None,
        very_verbose=None,
        mutators_to_run=None,
        comprehensive=None,
        codebase=(TEST_DATA_DIR / "test_source_unit" / "src" / "Counter.sol").as_posix(),
        contract_names="Counter",
    ),
)
@pytest.mark.skip(reason="Slow test")
def test_mutator(mock_args, solc_binary_path):  # pylint: disable=unused-argument

    with change_directory(TEST_DATA_DIR / "test_source_unit"):
        main()


def test_backup_source_file(solc_binary_path):
    solc_path = solc_binary_path("0.8.15")

    file_path = (TEST_DATA_DIR / "test_source_unit" / "src" / "Counter.sol").as_posix()
    sl = Slither(file_path, solc=solc_path, compile_force_framework="solc")

    with tempfile.TemporaryDirectory() as directory:
        files_dict = backup_source_file(sl.source_code, Path(directory))

        assert len(files_dict) == 1
        assert Path(files_dict[file_path]).exists()


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_get_sol_file_list():

    project_directory = TEST_DATA_DIR / "test_source_unit"

    files = get_sol_file_list(project_directory, None)

    assert len(files) == 46

    files = get_sol_file_list(project_directory, ["lib"])
    assert len(files) == 3

    files = get_sol_file_list(project_directory, ["lib", "script"])
    assert len(files) == 2

    files = get_sol_file_list(project_directory / "src" / "Counter.sol", None)
    assert len(files) == 1

    (project_directory / "test.sol").mkdir()
    files = get_sol_file_list(project_directory, None)
    assert all("test.sol" not in file for file in files)
    (project_directory / "test.sol").rmdir()


@pytest.mark.skipif(
    not foundry_available or not project_ready, reason="requires Foundry and project setup"
)
def test_run_test(caplog):
    with change_directory(TEST_DATA_DIR / "test_source_unit"):
        result = run_test_cmd("forge test", timeout=None, target_file=None, verbose=True)
        assert result
        assert not caplog.records

        # Failed command
        result = run_test_cmd("forge non-test", timeout=None, target_file=None, verbose=True)
        assert not result
        assert caplog.records


def test_run_tests_timeout(caplog, monkeypatch):
    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout"))

    monkeypatch.setattr(subprocess, "run", mock_run)

    with change_directory(TEST_DATA_DIR / "test_source_unit"):
        result = run_test_cmd("forge test", timeout=1)
        assert not result
        assert "Tests took too long" in caplog.messages[0]


def test_parse_target_selectors_hex():
    """Test hex selector parsing"""
    selectors = parse_target_selectors("0xa9059cbb")
    assert 0xA9059CBB in selectors
    assert len(selectors) == 1


def test_parse_target_selectors_signature():
    """Test signature to selector conversion"""
    selectors = parse_target_selectors("transfer(address,uint256)")
    expected = get_function_id("transfer(address,uint256)")
    assert expected in selectors
    assert len(selectors) == 1


def test_parse_target_selectors_multiple():
    """Test multiple selectors (mixed formats)"""
    selectors = parse_target_selectors("0xa9059cbb,mint(address,uint256)")
    assert len(selectors) == 2
    assert 0xA9059CBB in selectors
    assert get_function_id("mint(address,uint256)") in selectors


def test_parse_target_selectors_empty_parts():
    """Test handling of empty parts in comma-separated list"""
    selectors = parse_target_selectors("0xa9059cbb,,0x40c10f19")
    assert len(selectors) == 2


def test_parse_target_selectors_whitespace():
    """Test handling of whitespace around selectors"""
    # Note: 0xa9059cbb IS transfer(address,uint256), so deduped to 1
    selectors = parse_target_selectors("  0xa9059cbb  ,  mint(address,uint256)  ")
    assert len(selectors) == 2


def test_should_mutate_function_no_filter(solc_binary_path):
    """When target_selectors is None, all functions should be mutated"""
    solc_path = solc_binary_path("0.8.15")
    file_path = (TEST_DATA_DIR / "test_source_unit" / "src" / "Counter.sol").as_posix()
    sl = Slither(file_path, solc=solc_path, compile_force_framework="solc")

    contract = next(c for c in sl.contracts if c.name == "Counter")

    with tempfile.TemporaryDirectory() as tmpdir:
        mutator = RR(
            sl.compilation_units[0],
            timeout=30,
            testing_command="true",
            testing_directory=None,
            contract_instance=contract,
            solc_remappings=None,
            verbose=False,
            output_folder=Path(tmpdir),
            dont_mutate_line=[],
            target_selectors=None,
            target_modifiers=None,
        )

        # All functions should be included when no filter
        for func in contract.functions_declared:
            assert mutator.should_mutate_function(func) is True


def test_should_mutate_function_matching_selector(solc_binary_path):
    """Function matching target selector should be mutated"""
    solc_path = solc_binary_path("0.8.15")
    file_path = (TEST_DATA_DIR / "test_source_unit" / "src" / "Counter.sol").as_posix()
    sl = Slither(file_path, solc=solc_path, compile_force_framework="solc")

    contract = next(c for c in sl.contracts if c.name == "Counter")
    increment_selector = get_function_id("increment()")

    with tempfile.TemporaryDirectory() as tmpdir:
        mutator = RR(
            sl.compilation_units[0],
            timeout=30,
            testing_command="true",
            testing_directory=None,
            contract_instance=contract,
            solc_remappings=None,
            verbose=False,
            output_folder=Path(tmpdir),
            dont_mutate_line=[],
            target_selectors={increment_selector},
            target_modifiers=None,
        )

        for func in contract.functions_declared:
            if func.name == "increment":
                assert mutator.should_mutate_function(func) is True
            else:
                assert mutator.should_mutate_function(func) is False


def test_should_mutate_function_no_match(solc_binary_path):
    """Function not matching any selector should not be mutated"""
    solc_path = solc_binary_path("0.8.15")
    file_path = (TEST_DATA_DIR / "test_source_unit" / "src" / "Counter.sol").as_posix()
    sl = Slither(file_path, solc=solc_path, compile_force_framework="solc")

    contract = next(c for c in sl.contracts if c.name == "Counter")

    with tempfile.TemporaryDirectory() as tmpdir:
        mutator = RR(
            sl.compilation_units[0],
            timeout=30,
            testing_command="true",
            testing_directory=None,
            contract_instance=contract,
            solc_remappings=None,
            verbose=False,
            output_folder=Path(tmpdir),
            dont_mutate_line=[],
            target_selectors={0xDEADBEEF},
            target_modifiers=None,
        )

        # No functions should match bogus selector
        for func in contract.functions_declared:
            assert mutator.should_mutate_function(func) is False


def test_should_mutate_function_includes_modifier(solc_binary_path):
    """Modifier used by target function should be mutated"""
    solc_path = solc_binary_path("0.8.15")
    file_path = (TEST_DATA_DIR / "test_source_unit" / "src" / "Counter.sol").as_posix()
    sl = Slither(file_path, solc=solc_path, compile_force_framework="solc")

    contract = next(c for c in sl.contracts if c.name == "Counter")
    restricted_selector = get_function_id("restrictedIncrement()")

    with tempfile.TemporaryDirectory() as tmpdir:
        mutator = RR(
            sl.compilation_units[0],
            timeout=30,
            testing_command="true",
            testing_directory=None,
            contract_instance=contract,
            solc_remappings=None,
            verbose=False,
            output_folder=Path(tmpdir),
            dont_mutate_line=[],
            target_selectors={restricted_selector},
            target_modifiers={"onlyOwner"},
        )

        # onlyOwner modifier should be included
        for mod in contract.modifiers:
            if mod.name == "onlyOwner":
                assert mutator.should_mutate_function(mod) is True
