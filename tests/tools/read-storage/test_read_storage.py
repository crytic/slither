import re
import json
from pathlib import Path

import pytest
from deepdiff import DeepDiff
from web3.contract import Contract

from slither import Slither
from slither.tools.read_storage import SlitherReadStorage, RpcInfo

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


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
@pytest.mark.parametrize(
    "test_contract, storage_file",
    [("StorageLayout", "storage_layout"), ("UnstructuredStorageLayout", "unstructured_storage")],
)
@pytest.mark.usefixtures("web3", "ganache")
def test_read_storage(test_contract, storage_file, web3, ganache, solc_binary_path) -> None:
    solc_path = solc_binary_path(version="0.8.10")

    assert web3.is_connected()
    bin_path = Path(TEST_DATA_DIR, f"{test_contract}.bin").as_posix()
    abi_path = Path(TEST_DATA_DIR, f"{test_contract}.abi").as_posix()
    bytecode = get_source_file(bin_path)
    abi = get_source_file(abi_path)
    contract = deploy_contract(web3, ganache, bytecode, abi)
    contract.functions.store().transact({"from": ganache.eth_address})
    address = contract.address

    sl = Slither(Path(TEST_DATA_DIR, f"{test_contract}.sol").as_posix(), solc=solc_path)
    contracts = sl.contracts

    rpc_info: RpcInfo = RpcInfo(ganache.provider)
    srs = SlitherReadStorage(contracts, 100, rpc_info)
    srs.unstructured = True
    srs.storage_address = address
    srs.get_all_storage_variables()
    srs.get_storage_layout()
    srs.walk_slot_info(srs.get_slot_values)
    actual_file = Path(TEST_DATA_DIR, "storage_layout.json").as_posix()
    with open(actual_file, "w", encoding="utf-8") as file:
        slot_infos_json = srs.to_json()
        json.dump(slot_infos_json, file, indent=4)

    expected_file = Path(TEST_DATA_DIR, f"TEST_{storage_file}.json").as_posix()

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
                f.write(str(change.t1))
            with open(f"{path}_actual.txt", "w", encoding="utf8") as f:
                f.write(str(change.t2))

    assert not diff
