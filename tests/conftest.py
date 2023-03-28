import pytest
from filelock import FileLock
from solc_select import solc_select


@pytest.fixture(scope="session")
def solc_binary_path():
    def inner(version):
        lock = FileLock(f"{version}.lock", timeout=60)
        with lock:
            if not solc_select.artifact_path(version).exists():
                print("Installing solc version", version)
                solc_select.install_artifacts([version])
        return solc_select.artifact_path(version)

    return inner
