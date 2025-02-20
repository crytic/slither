from pathlib import Path
from slither import Slither

from slither.core.expressions import CallExpression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.local_variable import LocalVariable


TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_yul_parser_assembly_slot(solc_binary_path) -> None:
    # mstore(0x0, bucketId)
    # mstore(0x20, _counters.slot)
    data = {"0x0": "bucketId", "0x20": "_counters"}

    solc_path = solc_binary_path("0.8.18")
    slither = Slither(Path(TEST_DATA_DIR, "assembly_storage_slot.sol").as_posix(), solc=solc_path)

    contract = slither.get_contract_from_name("XXX")[0]
    func = contract.get_function_from_full_name("getPackedBucketGlobalState(uint256)")
    calls = [
        node.expression
        for node in func.all_nodes()
        if node.expression and "mstore" in str(node.expression)
    ]

    for call in calls:
        assert isinstance(call, CallExpression)
        memory_location = call.arguments[0]
        value = call.arguments[1]
        assert isinstance(memory_location, Literal)
        assert isinstance(value, Identifier)
        assert value.value.name == data[memory_location.value]
        if value.value.name == "_counters":
            assert isinstance(value.value, StateVariable)
        elif value.value.name == "bucketId":
            assert isinstance(value.value, LocalVariable)


def test_yul_parser_sstore_sload(solc_binary_path) -> None:

    solc_path = solc_binary_path("0.8.18")
    slither = Slither(Path(TEST_DATA_DIR, "assembly_sstore_sload.sol").as_posix(), solc=solc_path)

    contract = slither.get_contract_from_name("Test")[0]

    read = contract.get_function_from_full_name("read()")
    # Sload is converted to an assignement
    assert len(read.all_solidity_calls()) == 0

    read_parameter = contract.get_function_from_full_name("read_parameter(uint256)")
    # Sload is kept because the slot is dynamic
    assert len(read_parameter.all_solidity_calls()) == 1

    write = contract.get_function_from_full_name("write()")
    # Sstore is converted to an assignement
    assert len(write.all_solidity_calls()) == 0

    write_parameter = contract.get_function_from_full_name("write_parameter(uint256)")
    # Sstore is kept because the slot is dynamic
    assert len(write_parameter.all_solidity_calls()) == 1
