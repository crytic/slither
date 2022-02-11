import re
import os
import sys
import json
import pytest
import shutil
import subprocess
from time import sleep
from typing import Generator
from deepdiff import DeepDiff
from dataclasses import dataclass
from slither import Slither
from slither.tools.read_storage import get_storage_layout

try:
    from web3 import Web3
except ImportError:
    print("ERROR: in order to use slither-read-storage, you need to install web3")
    print("$ pip3 install web3 --user\n")
    sys.exit(-1)

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "storage-layout")


@dataclass
class GanacheInstance:
    provider: str
    eth_address: str
    eth_privkey: str


@pytest.fixture(scope="module")
def web3(ganache: GanacheInstance):
    w3 = Web3(Web3.HTTPProvider(ganache.provider, request_kwargs={"timeout": 30}))
    return w3


@pytest.fixture(scope="module")
def ganache() -> Generator[GanacheInstance, None, None]:
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
    p = subprocess.Popen(
        f"""ganache
        --port {port}
        --chain.networkId 1
        --chain.chainId 1
        --account {eth_privkey},{eth}
        """.replace(
            "\n", " "
        ),
        shell=True,
    )

    sleep(3)
    yield GanacheInstance(f"http://127.0.0.1:{port}", eth_address, eth_privkey)
    p.kill()
    p.wait()


def get_source_file(file_path):
    with open(file_path, "r") as f:
        source = f.read()

    return source


def deploy_contract(w3, ganache, contract_bin, contract_abi):
    """Deploy contract to the local ganache network"""
    print("balance", w3.eth.get_balance(ganache.eth_address))
    signed_txn = w3.eth.account.sign_transaction(
        dict(
            nonce=w3.eth.get_transaction_count(ganache.eth_address),
            maxFeePerGas=20000000000,
            maxPriorityFeePerGas=1,
            gas=15000000,
            to=b"",
            data="0x" + contract_bin,
            chainId=1,
        ),
        ganache.eth_privkey,
    )
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    address = w3.eth.get_transaction_receipt(tx_hash)["contractAddress"]
    contract = w3.eth.contract(address, abi=contract_abi)
    return contract


@pytest.mark.usefixtures("web3", "ganache")
def test_read_storage(web3, ganache):
    assert web3.isConnected()
    bin_path = os.path.join(STORAGE_TEST_ROOT, "StorageLayout.bin")
    abi_path = os.path.join(STORAGE_TEST_ROOT, "StorageLayout.abi")
    bin = get_source_file(bin_path)
    abi = get_source_file(abi_path)
    contract = deploy_contract(web3, ganache, bin, abi)
    contract.functions.store().transact({"from": ganache.eth_address})
    address = contract.address

    sl = Slither(os.path.join(STORAGE_TEST_ROOT, "storage_layout-0.8.10.sol"))
    contracts = sl.contracts

    get_storage_layout(contracts, address, ganache.provider, 20)
    expected_file = os.path.join(STORAGE_TEST_ROOT, "TEST_storage_layout.json")
    actual_file = os.path.join(SLITHER_ROOT, f"{address}_storage_layout.json")

    with open(expected_file, "r") as f:
        expected = json.load(f)
    with open(actual_file, "r") as f:
        actual = json.load(f)

    diff = DeepDiff(expected, actual, ignore_order=True, verbose_level=2, view="tree")
    if diff:
        for change in diff.get("values_changed", []):
            path_list = re.findall(r"\['(.*?)'\]", change.path())
            path = "_".join(path_list)
            with open(f"{path}_expected.txt", "w") as f:
                f.write(change.t1)
            with open(f"{path}_actual.txt", "w") as f:
                f.write(change.t2)

    assert not diff
