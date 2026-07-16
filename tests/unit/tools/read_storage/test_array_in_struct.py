"""
Tests for ArrayType support in slither-read-storage when arrays are inside structs.
Related to issue #1615.

Note: Tests are placed in tests/unit/tools/read_storage/ as they are unit tests
for specific functionality, unlike the integration tests in tests/tools/read-storage/.
"""

import os
import tempfile

from slither import Slither
from slither.tools.read_storage.read_storage import SlitherReadStorage


def test_array_in_struct_detection(solc_binary_path) -> None:
    """Test that arrays inside structs are properly detected and don't cause errors."""
    solc_path = solc_binary_path("0.8.10")

    # Test contract with array inside struct (from issue #1615)
    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestArrayType {
    struct Checkpoint {
        uint32 _blockNumber;
        uint224 _value;
    }

    struct History {
        Checkpoint[] _checkpoints;
    }

    History private _totalCheckpoints;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_array_type.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = slither.contracts

        srs = SlitherReadStorage(contracts, 20)

        # This should not raise an error anymore
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        # Check that we have slot info for _totalCheckpoints
        assert "_totalCheckpoints" in srs.slot_info, "Expected _totalCheckpoints in slot_info"
        info = srs.slot_info["_totalCheckpoints"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        # History struct contains a dynamic array, which takes 1 slot for length
        assert info.size == 256, f"Expected size 256 bits for dynamic array length, got {info.size}"
        assert info.offset == 0, f"Expected offset 0, got {info.offset}"
        # Check that _checkpoints member is in elems
        assert "_checkpoints" in info.elems, "Expected _checkpoints in struct elems"


def test_fixed_array_in_struct(solc_binary_path) -> None:
    """Test that fixed arrays inside structs are handled correctly."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestFixedArray {
    struct Data {
        uint256 id;
        uint128[4] values;  // Fixed array of 4 uint128
        uint256 timestamp;
    }

    Data private data;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_fixed_array.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = slither.contracts

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "data" in srs.slot_info, "Expected data in slot_info"
        info = srs.slot_info["data"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        # Struct members: id (slot 0), values (slots 1-2, 4 x uint128 = 64 bytes = 2 slots), timestamp (slot 3)
        assert "id" in info.elems, "Expected id in struct elems"
        assert "values" in info.elems, "Expected values in struct elems"
        assert "timestamp" in info.elems, "Expected timestamp in struct elems"
        # Verify id is at slot 0
        assert info.elems["id"].slot == 0, f"Expected id at slot 0, got {info.elems['id'].slot}"
        # Verify values (fixed array) is at slot 1
        assert info.elems["values"].slot == 1, (
            f"Expected values at slot 1, got {info.elems['values'].slot}"
        )
        # Verify timestamp is at slot 3 (after 2 slots for the array)
        assert info.elems["timestamp"].slot == 3, (
            f"Expected timestamp at slot 3, got {info.elems['timestamp'].slot}"
        )


def test_nested_struct_with_array(solc_binary_path) -> None:
    """Test nested structs containing arrays."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestNestedStruct {
    struct Inner {
        uint256[] dynamicArray;
        uint256 value;
    }

    struct Outer {
        Inner inner;
        uint256 id;
    }

    Outer private data;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_nested.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = slither.contracts

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "data" in srs.slot_info, "Expected data in slot_info"
        info = srs.slot_info["data"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        # Outer struct: inner (2 slots: dynamicArray length + value), id (1 slot)
        assert "inner" in info.elems, "Expected inner in struct elems"
        assert "id" in info.elems, "Expected id in struct elems"
        # Inner struct is at slot 0, takes 2 slots
        assert info.elems["inner"].slot == 0, (
            f"Expected inner at slot 0, got {info.elems['inner'].slot}"
        )
        # Nested struct size should be actual storage size (2 slots = 64 bytes = 512 bits)
        assert info.elems["inner"].size == 512, (
            f"Expected inner size 512 bits, got {info.elems['inner'].size}"
        )
        # id is at slot 2 (after inner struct)
        assert info.elems["id"].slot == 2, f"Expected id at slot 2, got {info.elems['id'].slot}"


def test_mapping_in_struct(solc_binary_path) -> None:
    """Test that mappings inside structs are handled correctly."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestMapping {
    struct UserData {
        uint256 id;
        mapping(address => uint256) balances;
        uint256 totalBalance;
    }

    UserData private userData;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_mapping.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = slither.contracts

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "userData" in srs.slot_info, "Expected userData in slot_info"
        info = srs.slot_info["userData"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        # Struct members: id (slot 0), balances (slot 1), totalBalance (slot 2)
        assert "id" in info.elems, "Expected id in struct elems"
        assert "balances" in info.elems, "Expected balances in struct elems"
        assert "totalBalance" in info.elems, "Expected totalBalance in struct elems"
        # Verify slots
        assert info.elems["id"].slot == 0, f"Expected id at slot 0, got {info.elems['id'].slot}"
        assert info.elems["balances"].slot == 1, (
            f"Expected balances at slot 1, got {info.elems['balances'].slot}"
        )
        assert info.elems["totalBalance"].slot == 2, (
            f"Expected totalBalance at slot 2, got {info.elems['totalBalance'].slot}"
        )


def test_enum_in_struct(solc_binary_path) -> None:
    """Test that enums inside structs are handled correctly (should pack like elementary types)."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestEnum {
    enum Status { Pending, Active, Completed }

    struct Task {
        uint64 id;
        Status status;  // Enum packs with id (both fit in one slot)
        uint64 timestamp;
        uint256 value;
    }

    Task private task;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_enum.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = slither.contracts

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "task" in srs.slot_info, "Expected task in slot_info"
        info = srs.slot_info["task"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        # Struct packing: id (64 bits) + status (8 bits) + timestamp (64 bits) = 136 bits, fits in slot 0
        # value (256 bits) is in slot 1
        assert "id" in info.elems, "Expected id in struct elems"
        assert "status" in info.elems, "Expected status in struct elems"
        assert "timestamp" in info.elems, "Expected timestamp in struct elems"
        assert "value" in info.elems, "Expected value in struct elems"
        # All of id, status, timestamp should be in slot 0 (packed)
        assert info.elems["id"].slot == 0, f"Expected id at slot 0, got {info.elems['id'].slot}"
        assert info.elems["status"].slot == 0, (
            f"Expected status at slot 0, got {info.elems['status'].slot}"
        )
        assert info.elems["timestamp"].slot == 0, (
            f"Expected timestamp at slot 0, got {info.elems['timestamp'].slot}"
        )
        # value should be in slot 1
        assert info.elems["value"].slot == 1, (
            f"Expected value at slot 1, got {info.elems['value'].slot}"
        )
        # Verify enum size (1 byte = 8 bits)
        assert info.elems["status"].size == 8, (
            f"Expected status size 8 bits, got {info.elems['status'].size}"
        )


def test_contract_type_in_struct(solc_binary_path) -> None:
    """Test that contract types inside structs are handled correctly (stored as address)."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function totalSupply() external view returns (uint256);
}

contract TestContractType {
    struct TokenInfo {
        IERC20 token;  // Contract type stored as address (20 bytes)
        uint96 balance;  // Can pack with token in same slot
    }

    TokenInfo private info;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_contract_type.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = slither.contracts

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "info" in srs.slot_info, "Expected info in slot_info"
        slot_info = srs.slot_info["info"]
        assert slot_info.slot == 0, f"Expected slot 0, got {slot_info.slot}"
        # Struct packing: token (160 bits) + balance (96 bits) = 256 bits, fits in slot 0
        assert "token" in slot_info.elems, "Expected token in struct elems"
        assert "balance" in slot_info.elems, "Expected balance in struct elems"
        # Both should be in slot 0 (packed)
        assert slot_info.elems["token"].slot == 0, (
            f"Expected token at slot 0, got {slot_info.elems['token'].slot}"
        )
        assert slot_info.elems["balance"].slot == 0, (
            f"Expected balance at slot 0, got {slot_info.elems['balance'].slot}"
        )
        # Verify contract type size (20 bytes = 160 bits, like address)
        assert slot_info.elems["token"].size == 160, (
            f"Expected token size 160 bits, got {slot_info.elems['token'].size}"
        )
        # Verify balance size (96 bits)
        assert slot_info.elems["balance"].size == 96, (
            f"Expected balance size 96 bits, got {slot_info.elems['balance'].size}"
        )
