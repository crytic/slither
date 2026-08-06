import re
import json
import sys
import subprocess
from pathlib import Path

import pytest
from deepdiff import DeepDiff
from web3.contract import Contract

from slither import Slither
from slither.tools.read_storage import SlitherReadStorage, RpcInfo
from slither.tools.read_storage.__main__ import _is_solc_standard_json

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def get_source_file(file_path) -> str:
    with open(file_path, encoding="utf8") as f:
        source = f.read()

    return source


def deploy_contract(w3, ganache, contract_bin, contract_abi) -> Contract:
    """Deploy contract to the local ganache network"""
    signed_txn = w3.eth.account.sign_transaction(
        {
            "nonce": w3.eth.get_transaction_count(ganache.eth_address),
            "maxFeePerGas": 20000000000,
            "maxPriorityFeePerGas": 1,
            "gas": 15000000,
            "to": b"",
            "data": "0x" + contract_bin,
            "chainId": 1,
        },
        ganache.eth_privkey,
    )
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    address = w3.eth.get_transaction_receipt(tx_hash)["contractAddress"]
    contract = w3.eth.contract(address, abi=contract_abi)
    return contract


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

    with open(expected_file, encoding="utf8") as f:
        expected = json.load(f)
    with open(actual_file, encoding="utf8") as f:
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


# --- Regression tests for GitHub issue #2777 -------------------------------
# slither-read-storage should accept a solc Standard JSON *input* file
# (https://docs.soliditylang.org/en/latest/using-the-compiler.html#input-description)
# directly as its target, without requiring --compile-force-framework solc-json.


def _build_standard_json(sol_path: Path) -> dict:
    """Wrap a .sol file's contents in a minimal solc Standard JSON input dict."""
    return {
        "language": "Solidity",
        "sources": {sol_path.name: {"content": get_source_file(sol_path.as_posix())}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "evm.bytecode", "evm.deployedBytecode", "devdoc", "userdoc"],
                    "": ["ast"],
                }
            }
        },
    }


@pytest.mark.parametrize(
    "existing_file, expected",
    [
        # Not JSON at all
        ("StorageLayout.sol", False),
        # A JSON file that isn't a solc Standard JSON input (missing "language"/"sources")
        ("not_standard.json", False),
        # A well-formed solc Standard JSON input
        ("standard_json_input.json", True),
    ],
)
def test_is_solc_standard_json(tmp_path, existing_file, expected) -> None:
    """`_is_solc_standard_json` should only return True for genuine Standard JSON input files,
    and must not raise on non-JSON, malformed JSON, or missing files."""

    if existing_file == "StorageLayout.sol":
        path = Path(TEST_DATA_DIR, existing_file).as_posix()
    elif existing_file == "not_standard.json":
        path = str(tmp_path / existing_file)
        with open(path, "w", encoding="utf8") as f:
            json.dump({"foo": "bar"}, f)
    else:
        path = str(tmp_path / existing_file)
        standard_json = _build_standard_json(Path(TEST_DATA_DIR, "StorageLayout.sol"))
        with open(path, "w", encoding="utf8") as f:
            json.dump(standard_json, f)

    assert _is_solc_standard_json(path) is expected

    # A nonexistent path must never raise, and must return False
    assert _is_solc_standard_json(str(tmp_path / "does_not_exist.json")) is False

    # Invalid JSON syntax must never raise, and must return False
    broken_path = tmp_path / "broken.json"
    broken_path.write_text("{not valid json", encoding="utf8")
    assert _is_solc_standard_json(str(broken_path)) is False


def test_read_storage_from_standard_json(tmp_path, solc_binary_path) -> None:
    """slither-read-storage's storage-layout extraction should work identically whether the
    contract is given as a plain .sol file or as a solc Standard JSON input file, with no
    extra flags required (i.e. Slither must auto-select the solc-json compilation platform).

    Note: the auto-detection lives in the CLI's main(), not in Slither.__init__ itself, so this
    exercises the actual slither-read-storage entrypoint (as issue #2777 did) rather than
    calling Slither() directly, which would bypass the fix.
    """

    solc_path = solc_binary_path(version="0.8.10")
    sol_path = Path(TEST_DATA_DIR, "StorageLayout.sol")

    # Write out a genuine solc Standard JSON input file, the same shape a user would get from
    # `solc --standard-json` tooling.
    standard_json_path = tmp_path / "StorageLayout.standard-json.json"
    with open(standard_json_path, "w", encoding="utf8") as f:
        json.dump(_build_standard_json(sol_path), f)

    def layout_via_cli(target: str, out_name: str) -> dict:
        out_path = tmp_path / out_name
        subprocess.run(
            [
                sys.executable,
                "-m",
                "slither.tools.read_storage",
                target,
                "--contract-name",
                "StorageLayout",
                "--solc",
                solc_path,
                "--json",
                str(out_path),
            ],
            cwd=TEST_DATA_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        with open(out_path, encoding="utf8") as f:
            return json.load(f)

    # Baseline: compiling the plain .sol file directly.
    expected_layout = layout_via_cli(sol_path.as_posix(), "expected.json")

    # This is the exact scenario from issue #2777: passing a Standard JSON file as the sole
    # target, with no --compile-force-framework flag, must work and produce the same layout.
    actual_layout = layout_via_cli(standard_json_path.as_posix(), "actual.json")

    diff = DeepDiff(expected_layout, actual_layout, ignore_order=True)
    assert not diff
