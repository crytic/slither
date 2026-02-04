// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Inline Assembly mstore/mload
/// @dev Tests basic memory write/read operations using assembly
contract Test_Mstore {
    /// @dev Stores a constant then loads it
    /// Input: none, Output: x = 42
    function test_store_load() public pure returns (uint256 x) {
        assembly {
            mstore(0, 42)
            x := mload(0)
        }
    }

    /// @dev Multiple stores then load - should be OR of values
    /// Output: x ∈ {42, 45}
    function test_store_load_multi() public pure returns (uint256 x) {
        assembly {
            mstore(0, 42)
            mstore(0, 45)
            x := mload(0)
        }
    }

    /// @dev Store to different offsets
    /// Output: x = 10, y = 20
    function test_different_offsets() public pure returns (uint256 x, uint256 y) {
        assembly {
            mstore(0, 10)
            mstore(32, 20)
            x := mload(0)
            y := mload(32)
        }
    }

    /// @dev Store parameter then load
    /// Input: value [0, 2^256-1], Output: x = value
    function test_store_param(uint256 value) public pure returns (uint256 x) {
        assembly {
            mstore(0, value)
            x := mload(0)
        }
    }

    /// @dev Store at dynamic offset with dynamic value
    /// Input: offset [0, 2^256-1], value [0, 2^256-1], Output: x = value
    function test_store_dynamic(uint256 offset, uint256 value) public pure returns (uint256 x) {
        assembly {
            mstore(add(32, offset), value)
            x := mload(offset)
        }
    }
}
