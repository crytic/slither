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
from slither.tools.mutator.__main__ import _get_mutators, main
from slither.tools.mutator.utils.testing_generated_mutant import run_test_cmd
from slither.tools.mutator.utils.file_handling import get_sol_file_list, backup_source_file


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
    sl = Slither(file_path, solc=solc_path)

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
