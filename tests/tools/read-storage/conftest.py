"""
Testing utilities for the read-storage tool
"""

import shutil
import subprocess
from time import sleep
from typing import Generator
from dataclasses import dataclass
from web3 import Web3
import pytest


@dataclass
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
