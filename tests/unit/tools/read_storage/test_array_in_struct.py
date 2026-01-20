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
        assert len(srs.slot_info) > 0, "Expected slot info to be populated"


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

        assert len(srs.slot_info) > 0, "Expected slot info to be populated"


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

        assert len(srs.slot_info) > 0, "Expected slot info to be populated"


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

        assert len(srs.slot_info) > 0, "Expected slot info to be populated"


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

        assert len(srs.slot_info) > 0, "Expected slot info to be populated"


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

        assert len(srs.slot_info) > 0, "Expected slot info to be populated"
