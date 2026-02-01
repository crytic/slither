// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Bit Shift Operations
/// @dev Tests interval analysis for shift operations (left and right)
contract Test_Shift {
    // ============ Left Shift (<<) ============

    /// @dev Input: x in [0, 2^256-1], Output: x * 2
    function test_shl_one(uint256 x) public pure returns (uint256) {
        return x << 1;
    }

    /// @dev Input: x in [0, 2^256-1], Output: x * 4
    function test_shl_two(uint256 x) public pure returns (uint256) {
        return x << 2;
    }

    /// @dev Input: known value, Output: exact result [40, 40]
    function test_shl_constant() public pure returns (uint256) {
        uint256 a = 10;
        return a << 2;
    }

    /// @dev Variable shift amount
    function test_shl_variable(uint256 x, uint256 y) public pure returns (uint256) {
        return x << y;
    }

    // ============ Right Shift (>>) ============

    /// @dev Input: x in [0, 2^256-1], Output: x / 2
    function test_shr_one(uint256 x) public pure returns (uint256) {
        return x >> 1;
    }

    /// @dev Input: x in [0, 2^256-1], Output: x / 4
    function test_shr_two(uint256 x) public pure returns (uint256) {
        return x >> 2;
    }

    /// @dev Input: known value, Output: exact result [2, 2]
    function test_shr_constant() public pure returns (uint256) {
        uint256 a = 10;
        return a >> 2;
    }

    /// @dev Variable shift amount
    function test_shr_variable(uint256 x, uint256 y) public pure returns (uint256) {
        return x >> y;
    }

    // ============ Signed Right Shift (arithmetic) ============

    /// @dev Signed: preserves sign bit
    function test_sar_one(int256 x) public pure returns (int256) {
        return x >> 1;
    }

    /// @dev Signed: negative value
    function test_sar_negative() public pure returns (int256) {
        int256 a = -10;
        return a >> 2;
    }

    /// @dev Signed: variable shift
    function test_sar_variable(int256 x, uint256 y) public pure returns (int256) {
        return x >> y;
    }
}
