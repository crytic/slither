# pylint: disable=unused-import,redefined-outer-name
import os
import sys
import shutil
import subprocess
import tempfile
from time import sleep
from typing import Generator
from pathlib import Path
from contextlib import contextmanager
from filelock import FileLock
from solc_select import solc_select
from slither import Slither
from web3 import Web3
import pytest


# pylint: disable=too-few-public-methods
class GanacheInstance:
    def __init__(self, provider: str, eth_address: str, eth_privkey: str):
        self.provider = provider
        self.eth_address = eth_address
        self.eth_privkey = eth_privkey


@pytest.fixture(scope="module", name="ganache")
def fixture_ganache() -> Generator[GanacheInstance, None, None]:
    """Fixture that runs ganache"""
    if not shutil.which("ganache"):
        raise Exception(
            "ganache was not found in PATH, you can install it with `npm install -g ganache`"
        )

    # Address #1 when ganache is run with `--wallet.seed test`, it starts with 1000 ETH
    eth_address = "0xae17D2dD99e07CA3bF2571CCAcEAA9e2Aefc2Dc6"
    eth_privkey = "0xe48ba530a63326818e116be262fd39ae6dcddd89da4b1f578be8afd4e8894b8d"
    eth = int(1e18 * 1e6)
    port = 8545
    with subprocess.Popen(
        f"""ganache
        --port {port}
        --chain.networkId 1
        --chain.chainId 1
        --account {eth_privkey},{eth}
        """.replace(
            "\n", " "
        ),
        shell=True,
    ) as p:

        sleep(3)
        yield GanacheInstance(f"http://127.0.0.1:{port}", eth_address, eth_privkey)
        p.kill()
        p.wait()


@pytest.fixture(scope="module", name="web3")
def fixture_web3(ganache: GanacheInstance):
    w3 = Web3(Web3.HTTPProvider(ganache.provider, request_kwargs={"timeout": 30}))
    return w3


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
def slither_from_source(solc_binary_path):
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

