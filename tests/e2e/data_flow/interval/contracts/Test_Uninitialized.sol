// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Uninitialized Variables (Zero-Initialized)
/// @dev In Solidity, uninitialized local variables have default zero values
contract Test_Uninitialized {
    // =========================================================================
    // Unsigned Integers - All should be [0, 0]
    // =========================================================================

    /// @dev Uninitialized uint256: expected [0, 0]
    function test_uint256() public pure returns (uint256) {
        uint256 x;
        return x;
    }

    /// @dev Uninitialized uint8: expected [0, 0]
    function test_uint8() public pure returns (uint8) {
        uint8 x;
        return x;
    }

    /// @dev Uninitialized uint16: expected [0, 0]
    function test_uint16() public pure returns (uint16) {
        uint16 x;
        return x;
    }

    /// @dev Uninitialized uint32: expected [0, 0]
    function test_uint32() public pure returns (uint32) {
        uint32 x;
        return x;
    }

    /// @dev Uninitialized uint64: expected [0, 0]
    function test_uint64() public pure returns (uint64) {
        uint64 x;
        return x;
    }

    /// @dev Uninitialized uint128: expected [0, 0]
    function test_uint128() public pure returns (uint128) {
        uint128 x;
        return x;
    }

    // =========================================================================
    // Signed Integers - All should be [0, 0]
    // =========================================================================

    /// @dev Uninitialized int256: expected [0, 0]
    function test_int256() public pure returns (int256) {
        int256 x;
        return x;
    }

    /// @dev Uninitialized int8: expected [0, 0]
    function test_int8() public pure returns (int8) {
        int8 x;
        return x;
    }

    /// @dev Uninitialized int16: expected [0, 0]
    function test_int16() public pure returns (int16) {
        int16 x;
        return x;
    }

    /// @dev Uninitialized int32: expected [0, 0]
    function test_int32() public pure returns (int32) {
        int32 x;
        return x;
    }

    /// @dev Uninitialized int64: expected [0, 0]
    function test_int64() public pure returns (int64) {
        int64 x;
        return x;
    }

    /// @dev Uninitialized int128: expected [0, 0]
    function test_int128() public pure returns (int128) {
        int128 x;
        return x;
    }

    // =========================================================================
    // Boolean - Should be [0, 0] (false)
    // =========================================================================

    /// @dev Uninitialized bool: expected [0, 0] (false)
    function test_bool() public pure returns (bool) {
        bool x;
        return x;
    }

    // =========================================================================
    // Address - Should be [0, 0] (zero address)
    // =========================================================================

    /// @dev Uninitialized address: expected [0, 0]
    function test_address() public pure returns (address) {
        address x;
        return x;
    }

    // =========================================================================
    // Bytes - Should be [0, 0]
    // =========================================================================

    /// @dev Uninitialized bytes1: expected [0, 0]
    function test_bytes1() public pure returns (bytes1) {
        bytes1 x;
        return x;
    }

    /// @dev Uninitialized bytes32: expected [0, 0]
    function test_bytes32() public pure returns (bytes32) {
        bytes32 x;
        return x;
    }

    // =========================================================================
    // Usage Patterns
    // =========================================================================

    /// @dev Uninitialized then assigned: expected [42, 42]
    function test_assign_after() public pure returns (uint256) {
        uint256 x;
        x = 42;
        return x;
    }

    /// @dev Uninitialized used in arithmetic: 0 + 10 = [10, 10]
    function test_add_to_zero() public pure returns (uint256) {
        uint256 x;
        uint256 result = x + 10;
        return result;
    }

    /// @dev Multiple uninitialized: 0 + 0 = [0, 0]
    function test_two_uninitialized() public pure returns (uint256) {
        uint256 a;
        uint256 b;
        return a + b;
    }
}
