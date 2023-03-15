import re
import os
import json

import pytest
from deepdiff import DeepDiff
from slither import Slither
from slither.tools.read_storage import SlitherReadStorage
from tests.test_read_storage import get_source_file, deploy_contract

SLITHER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_TEST_ROOT = os.path.join(SLITHER_ROOT, "tests", "storage-layout")


# pylint: disable=too-many-locals
@pytest.mark.usefixtures("web3", "ganache")
def test_read_storage(web3, ganache) -> None:
    assert web3.isConnected()
    bin_path = os.path.join(STORAGE_TEST_ROOT, "UnstructuredStorageLayout.bin")
    abi_path = os.path.join(STORAGE_TEST_ROOT, "UnstructuredStorageLayout.abi")
    bytecode = get_source_file(bin_path)
    abi = get_source_file(abi_path)
    contract = deploy_contract(web3, ganache, bytecode, abi)
    contract.functions.store().transact({"from": ganache.eth_address})
    address = contract.address

    sl = Slither(os.path.join(STORAGE_TEST_ROOT, "unstructured_storage-0.8.10.sol"))
    contracts = sl.contracts

    srs = SlitherReadStorage(contracts, 100)
    srs.rpc = ganache.provider
    srs.storage_address = address
    srs.get_all_storage_variables()
    srs.get_storage_layout()
    srs.walk_slot_info(srs.get_slot_values)
    with open("unstructured_storage.json", "w", encoding="utf-8") as file:
        slot_infos_json = srs.to_json()
        json.dump(slot_infos_json, file, indent=4)

    expected_file = os.path.join(STORAGE_TEST_ROOT, "TEST_unstructured_storage.json")
    actual_file = os.path.join(SLITHER_ROOT, "unstructured_storage.json")

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
