# pylint: disable=redefined-outer-name
from pathlib import Path
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
import pytest
from filelock import FileLock
from solc_select import solc_select
from slither import Slither


@pytest.fixture()
def solc_binary_path():
    def inner(version):
        lock = FileLock(f"{version}.lock", timeout=60)
        with lock:
            if not solc_select.artifact_path(version).exists():
                print("Installing solc version", version)
                solc_select.install_artifacts([version])
        return solc_select.artifact_path(version)

    return inner


@pytest.fixture()
def slither_from_source(solc_binary_path):
    @contextmanager
    def inner(source_code: str, solc_version: str = "0.8.19"):
        """Yields a Slither instance using source_code string and solc_version

        Creates a temporary file and changes the solc-version temporary to solc_version.
        """

        fname = ""
        try:
            with NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as f:
                fname = f.name
                f.write(source_code)
            solc_path = solc_binary_path(solc_version)
            yield Slither(fname, solc=solc_path)
        finally:
            Path(fname).unlink()

    return inner
