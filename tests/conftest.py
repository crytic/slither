# pylint: disable=redefined-outer-name
import os
import shutil
import tempfile
from pathlib import Path
from contextlib import contextmanager
from filelock import FileLock
from solc_select import solc_select
import pytest
from slither import Slither


def pytest_configure(config):
    """Create a temporary directory for the tests to use."""
    if is_master():
        config.stash["shared_directory"] = tempfile.mkdtemp()


def pytest_unconfigure(config):
    """Remove the temporary directory after the tests are done."""
    if is_master():
        shutil.rmtree(config.stash["shared_directory"])


def pytest_configure_node(node):
    """Configure each worker node with the shared directory."""
    node.workerinput["shared_directory"] = node.config.stash["shared_directory"]


def is_master():
    """Returns True if the current process is the master process (which does not have a worker id)."""
    return os.environ.get("PYTEST_XDIST_WORKER") is None


@pytest.fixture
def shared_directory(request):
    """Returns the shared directory for the current process."""
    if is_master():
        return request.config.stash["shared_directory"]
    return request.config.workerinput["shared_directory"]


@pytest.fixture
def solc_binary_path(shared_directory):
    """
    Returns the path to the solc binary for the given version.
    If the binary is not installed, it will be installed.
    """

    def inner(version):
        lock = FileLock(f"{shared_directory}/{version}.lock", timeout=60)
        with lock:
            if not solc_select.artifact_path(version).exists():
                print("Installing solc version", version)
                solc_select.install_artifacts([version])
        return solc_select.artifact_path(version).as_posix()

    return inner


@pytest.fixture
def slither_from_solidity_source(solc_binary_path):
    @contextmanager
    def inner(source_code: str, solc_version: str = "0.8.19"):
        """Yields a Slither instance using source_code string and solc_version.
        Creates a temporary file and compiles with solc_version.
        """

        fname = ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as f:
                fname = f.name
                f.write(source_code)
            solc_path = solc_binary_path(solc_version)
            yield Slither(fname, solc=solc_path)
        finally:
            Path(fname).unlink()

    return inner


@pytest.fixture
def slither_from_vyper_source():
    @contextmanager
    def inner(source_code: str):
        """Yields a Slither instance using source_code string.
        Creates a temporary file and compiles with vyper.
        """

        fname = ""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".vy", delete=False) as f:
                fname = f.name
                f.write(source_code)
            yield Slither(fname)
        finally:
            Path(fname).unlink()

    return inner
