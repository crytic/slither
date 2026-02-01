// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Assignment Operations Only
/// @dev Tests interval analysis for basic assignments
contract Test_Assignment {
    /// @dev Simple constant assignment
    function test_constant() public pure returns (uint256) {
        uint256 x = 5;
        return x;
    }

    /// @dev Variable to variable assignment
    function test_var_to_var() public pure returns (uint256) {
        uint256 x = 10;
        uint256 y = x;
        return y;
    }

    /// @dev Chain of assignments
    function test_chain() public pure returns (uint256) {
        uint256 a = 1;
        uint256 b = a;
        uint256 c = b;
        return c;
    }

    // ===== Unsigned Integer Types =====

    /// @dev uint8 assignment (8-bit)
    function test_uint8() public pure returns (uint8) {
        uint8 x = 255;
        return x;
    }

    /// @dev uint16 assignment (16-bit)
    function test_uint16() public pure returns (uint16) {
        uint16 x = 65535;
        return x;
    }

    /// @dev uint64 assignment (64-bit)
    function test_uint64() public pure returns (uint64) {
        uint64 x = 1000000;
        return x;
    }

    /// @dev uint128 assignment (128-bit)
    function test_uint128() public pure returns (uint128) {
        uint128 x = 340282366920938463463374607431768211455;
        return x;
    }

    // ===== Signed Integer Types (positive values only - no Binary op) =====

    /// @dev int8 assignment (8-bit signed, positive)
    function test_int8() public pure returns (int8) {
        int8 x = 127;
        return x;
    }

    /// @dev int16 assignment (16-bit signed, positive)
    function test_int16() public pure returns (int16) {
        int16 x = 32767;
        return x;
    }

    /// @dev int64 assignment (64-bit signed, positive)
    function test_int64() public pure returns (int64) {
        int64 x = 1000000;
        return x;
    }

    /// @dev int128 assignment (128-bit signed, positive)
    function test_int128() public pure returns (int128) {
        int128 x = 170141183460469231731687303715884105727;
        return x;
    }

    /// @dev int256 assignment (256-bit signed, positive)
    function test_int256() public pure returns (int256) {
        int256 x = 1;
        return x;
    }

    // ===== Bytes Types =====

    /// @dev bytes1 assignment (1 byte)
    function test_bytes1() public pure returns (bytes1) {
        bytes1 x = 0xff;
        return x;
    }

    /// @dev bytes4 assignment (4 bytes)
    function test_bytes4() public pure returns (bytes4) {
        bytes4 x = 0xdeadbeef;
        return x;
    }

    /// @dev bytes16 assignment (16 bytes)
    function test_bytes16() public pure returns (bytes16) {
        bytes16 x = 0x0102030405060708090a0b0c0d0e0f10;
        return x;
    }

    /// @dev bytes32 assignment (32 bytes)
    function test_bytes32() public pure returns (bytes32) {
        bytes32 x = 0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20;
        return x;
    }

    // ===== Address Types =====

    /// @dev address assignment
    function test_address() public pure returns (address) {
        address x = 0xdEad000000000000000000000000000000000000;
        return x;
    }

    // ===== Boolean Types =====

    /// @dev bool true assignment
    function test_bool_true() public pure returns (bool) {
        bool x = true;
        return x;
    }

    /// @dev bool false assignment
    function test_bool_false() public pure returns (bool) {
        bool x = false;
        return x;
    }
}
