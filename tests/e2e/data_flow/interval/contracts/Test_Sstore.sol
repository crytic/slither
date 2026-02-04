// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Inline Assembly sstore
/// @dev Tests basic storage write operations using assembly
contract Test_Sstore {
    uint256 public storedValue;

    /// @dev Stores a constant value at slot 0
    /// Input: none, Output: slot 0 = 42
    function test_store_constant() public {
        assembly {
            sstore(0, 42)
        }
    }

    /// @dev Stores input parameter at slot 0
    /// Input: value [0, 2^256-1], Output: slot 0 = value
    function test_store_param(uint256 value) public {
        assembly {
            sstore(0, value)
        }
    }

    /// @dev Stores computed value (addition) at slot 0
    /// Input: a [0, 2^256-1], b [0, 2^256-1], Output: slot 0 = a + b
    function test_store_add(uint256 a, uint256 b) public {
        assembly {
            sstore(0, add(a, b))
        }
    }

    /// @dev Stores then loads from slot 0
    /// Output: x = 42
    function test_store_load() public returns (uint256 x) {
        assembly {
            sstore(0, 42)
            x := sload(0)
        }
    }

    /// @dev Multiple stores then load - should be OR of values
    /// Output: x ∈ {42, 45}
    function test_store_load_multi() public returns (uint256 x) {
        assembly {

            sstore(0, 42)
            sstore(0, 45)
            sstore(0,100)
            x := sload(0)
        }
    }
}
