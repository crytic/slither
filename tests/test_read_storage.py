import dataclasses
import re
import os
import sys
import json
import shutil
import subprocess
from time import sleep
from typing import Generator

import pytest
from deepdiff import DeepDiff
from slither import Slither
from slither.tools.read_storage import SlitherReadStorage

try:
    from web3 import Web3
    from web3.contract import Contract
except ImportError:
    print("ERROR: in order to use slither-read-storage, you need to install web3")
    print("$ pip3 install web3 --user\n")
    sys.exit(-1)

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "storage-layout")

# pylint: disable=too-few-public-methods
class GanacheInstance:
    def __init__(self, provider: str, eth_address: str, eth_privkey: str):
        self.provider = provider
        self.eth_address = eth_address
        self.eth_privkey = eth_privkey


@pytest.fixture(scope="module", name="web3")
def fixture_web3(ganache: GanacheInstance):
    w3 = Web3(Web3.HTTPProvider(ganache.provider, request_kwargs={"timeout": 30}))
    return w3


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


def get_source_file(file_path) -> str:
    with open(file_path, "r", encoding="utf8") as f:
        source = f.read()

    return source


def deploy_contract(w3, ganache, contract_bin, contract_abi) -> Contract:
    """Deploy contract to the local ganache network"""
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


# pylint: disable=too-many-locals
@pytest.mark.usefixtures("web3", "ganache")
def test_read_storage(web3, ganache) -> None:
    assert web3.isConnected()
    bin_path = os.path.join(STORAGE_TEST_ROOT, "StorageLayout.bin")
    abi_path = os.path.join(STORAGE_TEST_ROOT, "StorageLayout.abi")
    bytecode = get_source_file(bin_path)
    abi = get_source_file(abi_path)
    contract = deploy_contract(web3, ganache, bytecode, abi)
    contract.functions.store().transact({"from": ganache.eth_address})
    address = contract.address

    sl = Slither(os.path.join(STORAGE_TEST_ROOT, "storage_layout-0.8.10.sol"))
    contracts = sl.contracts

    srs = SlitherReadStorage(contracts, 100)
    srs.rpc = ganache.provider
    srs.storage_address = address
    srs.get_all_storage_variables()
    srs.get_storage_layout()
    srs.get_slot_values()
    with open("storage_layout.json", "w", encoding="utf-8") as file:
        slot_infos_json = {key: dataclasses.asdict(value) for key, value in srs.slot_info.items()}
        json.dump(slot_infos_json, file, indent=4)

    expected_file = os.path.join(STORAGE_TEST_ROOT, "TEST_storage_layout.json")
    actual_file = os.path.join(SLITHER_ROOT, "storage_layout.json")

    with open(expected_file, "r", encoding="utf8") as f:
        expected = json.load(f)
    with open(actual_file, "r", encoding="utf8") as f:
        actual = json.load(f)

    diff = DeepDiff(expected, actual, ignore_order=True, verbose_level=2, view="tree")
    if diff:
        for change in diff.get("values_changed", []):
            path_list = re.findall(r"\['(.*?)'\]", change.path())
            path = "_".join(path_list)
            with open(f"{path}_expected.txt", "w", encoding="utf8") as f:
                f.write(change.t1)
            with open(f"{path}_actual.txt", "w", encoding="utf8") as f:
                f.write(change.t2)

    assert not diff
