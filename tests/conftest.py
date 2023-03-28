import pytest
from filelock import FileLock
from solc_select import solc_select

@pytest.fixture(scope="session")
def solc_versions_installed():
    """List of solc versions available in the test environment."""
    return []

@pytest.fixture(scope="session", autouse=True)
def register_solc_versions_installed(solc_versions_installed):
    solc_versions_installed.extend(solc_select.installed_versions())

@pytest.fixture(scope="session")
def use_solc_version(request, solc_versions_installed):
    def _use_solc_version(version):
        print(version)
        if version not in solc_versions_installed:
            print("Installing solc version", version)
            solc_select.install_artifacts([version])
        artifact_path = solc_select.artifact_path(version)
        lock = FileLock(artifact_path)
        try:
            yield artifact_path
        finally:
            lock.release()
    return _use_solc_version
