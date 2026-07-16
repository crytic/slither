"""
Tests for TypeAlias (user-defined value types) support in slither-read-storage.

User-defined value types were introduced in Solidity 0.8.8 with syntax: `type T is uint256`
These tests verify that read_storage correctly handles TypeAlias in:
- Simple storage variables
- Dynamic and fixed arrays
- Mappings (as key and value)
- Struct members (including packing)
"""

import os
import tempfile

from slither import Slither
from slither.tools.read_storage.read_storage import SlitherReadStorage


def test_type_alias_simple_storage(solc_binary_path) -> None:
    """Test TypeAlias as direct state variables."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

type MyUint256 is uint256;
type MyUint64 is uint64;
type MyAddress is address;

contract TestSimpleTypeAlias {
    MyUint256 value256;      // slot 0 (256 bits, full slot)
    MyUint64 value64;        // slot 1, offset 0 (64 bits)
    MyAddress owner;         // slot 1, offset 64 (160 bits, packs with value64)
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_simple_type_alias.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = [c for c in slither.contracts if c.name == "TestSimpleTypeAlias"]

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        # Verify value256 (MyUint256 -> uint256, 256 bits)
        assert "value256" in srs.slot_info, "Expected value256 in slot_info"
        info = srs.slot_info["value256"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        assert info.size == 256, f"Expected size 256 bits, got {info.size}"
        assert info.offset == 0, f"Expected offset 0, got {info.offset}"

        # Verify value64 (MyUint64 -> uint64, 64 bits)
        assert "value64" in srs.slot_info, "Expected value64 in slot_info"
        info = srs.slot_info["value64"]
        assert info.slot == 1, f"Expected slot 1, got {info.slot}"
        assert info.size == 64, f"Expected size 64 bits, got {info.size}"
        assert info.offset == 0, f"Expected offset 0, got {info.offset}"

        # Verify owner (MyAddress -> address, 160 bits) - packs with value64 in slot 1
        assert "owner" in srs.slot_info, "Expected owner in slot_info"
        info = srs.slot_info["owner"]
        assert info.slot == 1, f"Expected slot 1, got {info.slot}"
        assert info.size == 160, f"Expected size 160 bits, got {info.size}"
        assert info.offset == 64, f"Expected offset 64, got {info.offset}"


def test_type_alias_dynamic_array(solc_binary_path) -> None:
    """Test TypeAlias in dynamic arrays."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

type MyUint64 is uint64;

contract TestDynamicArray {
    MyUint64[] values;  // Dynamic array, slot 0 holds length
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_dynamic_array.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = [c for c in slither.contracts if c.name == "TestDynamicArray"]

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "values" in srs.slot_info, "Expected values in slot_info"
        info = srs.slot_info["values"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        # Dynamic array base slot holds length (256 bits)
        assert info.size == 256, f"Expected size 256 bits for array length, got {info.size}"


def test_type_alias_fixed_array(solc_binary_path) -> None:
    """Test TypeAlias in fixed-size arrays."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

type MyUint128 is uint128;

contract TestFixedArray {
    MyUint128[4] values;  // 4 x 128 bits = 512 bits = 2 slots
    uint256 afterArray;   // Should be at slot 2
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_fixed_array.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = [c for c in slither.contracts if c.name == "TestFixedArray"]

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "values" in srs.slot_info, "Expected values in slot_info"
        info = srs.slot_info["values"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"

        # afterArray should be at slot 2 (after 2 slots for the fixed array)
        assert "afterArray" in srs.slot_info, "Expected afterArray in slot_info"
        info = srs.slot_info["afterArray"]
        assert info.slot == 2, f"Expected slot 2, got {info.slot}"


def test_type_alias_mapping_value(solc_binary_path) -> None:
    """Test TypeAlias as mapping value type."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

type MyUint256 is uint256;

contract TestMappingValue {
    mapping(address => MyUint256) balances;  // slot 0
    uint256 totalSupply;                     // slot 1
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_mapping_value.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = [c for c in slither.contracts if c.name == "TestMappingValue"]

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "balances" in srs.slot_info, "Expected balances in slot_info"
        info = srs.slot_info["balances"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"
        # Mapping occupies 1 slot for its base position
        assert info.size == 256, f"Expected size 256, got {info.size}"

        # Verify totalSupply is at slot 1
        assert "totalSupply" in srs.slot_info, "Expected totalSupply in slot_info"
        info = srs.slot_info["totalSupply"]
        assert info.slot == 1, f"Expected slot 1, got {info.slot}"


def test_type_alias_mapping_key(solc_binary_path) -> None:
    """Test TypeAlias as mapping key type."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

type MyAddress is address;

contract TestMappingKey {
    mapping(MyAddress => uint256) balances;  // slot 0
    uint256 count;                           // slot 1
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_mapping_key.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = [c for c in slither.contracts if c.name == "TestMappingKey"]

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "balances" in srs.slot_info, "Expected balances in slot_info"
        info = srs.slot_info["balances"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"

        # Verify count is at slot 1
        assert "count" in srs.slot_info, "Expected count in slot_info"
        info = srs.slot_info["count"]
        assert info.slot == 1, f"Expected slot 1, got {info.slot}"


def test_type_alias_nested_mapping(solc_binary_path) -> None:
    """Test TypeAlias in nested mapping structure."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

type MyUint64 is uint64;

contract TestNestedMapping {
    mapping(address => mapping(MyUint64 => bool)) approvals;  // slot 0
    uint256 version;                                          // slot 1
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_nested_mapping.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = [c for c in slither.contracts if c.name == "TestNestedMapping"]

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "approvals" in srs.slot_info, "Expected approvals in slot_info"
        info = srs.slot_info["approvals"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"

        # Verify version is at slot 1
        assert "version" in srs.slot_info, "Expected version in slot_info"
        info = srs.slot_info["version"]
        assert info.slot == 1, f"Expected slot 1, got {info.slot}"


def test_type_alias_in_struct(solc_binary_path) -> None:
    """Test TypeAlias inside structs, verifying packing behavior."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.8;

type MyUint64 is uint64;
type MyBool is bool;

contract TestStructTypeAlias {
    struct PackedData {
        MyUint64 a;    // 64 bits, offset 0
        MyBool b;      // 8 bits, offset 64
        MyUint64 c;    // 64 bits, offset 72
        // Total: 136 bits, fits in slot 0
    }

    PackedData packed;  // slot 0
    uint256 afterStruct;  // slot 1
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_struct_type_alias.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = [c for c in slither.contracts if c.name == "TestStructTypeAlias"]

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "packed" in srs.slot_info, "Expected packed in slot_info"
        info = srs.slot_info["packed"]
        assert info.slot == 0, f"Expected slot 0, got {info.slot}"

        # Verify struct members exist
        assert "a" in info.elems, "Expected 'a' in struct elems"
        assert "b" in info.elems, "Expected 'b' in struct elems"
        assert "c" in info.elems, "Expected 'c' in struct elems"

        # Verify packing: all members in slot 0
        assert info.elems["a"].slot == 0, f"Expected 'a' at slot 0, got {info.elems['a'].slot}"
        assert info.elems["b"].slot == 0, f"Expected 'b' at slot 0, got {info.elems['b'].slot}"
        assert info.elems["c"].slot == 0, f"Expected 'c' at slot 0, got {info.elems['c'].slot}"

        # Verify sizes (from underlying types)
        assert info.elems["a"].size == 64, f"Expected 'a' size 64, got {info.elems['a'].size}"
        assert info.elems["b"].size == 8, f"Expected 'b' size 8, got {info.elems['b'].size}"
        assert info.elems["c"].size == 64, f"Expected 'c' size 64, got {info.elems['c'].size}"

        # Verify offsets
        assert info.elems["a"].offset == 0, f"Expected 'a' offset 0, got {info.elems['a'].offset}"
        assert info.elems["b"].offset == 64, f"Expected 'b' offset 64, got {info.elems['b'].offset}"
        assert info.elems["c"].offset == 72, f"Expected 'c' offset 72, got {info.elems['c'].offset}"

        # Verify afterStruct is at slot 1
        assert "afterStruct" in srs.slot_info, "Expected afterStruct in slot_info"
        info = srs.slot_info["afterStruct"]
        assert info.slot == 1, f"Expected slot 1, got {info.slot}"
