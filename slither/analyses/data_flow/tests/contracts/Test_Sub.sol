// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Subtraction Operations
/// @dev Tests interval analysis for sub operations (unsigned and signed)
contract Test_Sub {
    // ============ Unsigned Subtraction ============

    /// @dev Input: x in [0, 2^256-1], underflow constrained
    function test_sub_one(uint256 x) public pure returns (uint256) {
        return x - 1;
    }

    /// @dev Input: x,y in [0, 2^256-1]
    function test_sub_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
        return x - y;
    }

    /// @dev Input: known values, Output: exact result [5, 5]
    function test_sub_constants() public pure returns (uint256) {
        uint256 a = 15;
        uint256 b = 10;
        return a - b;
    }

    /// @dev Input: x in [0, 2^256-1], subtracting zero (identity)
    function test_sub_zero(uint256 x) public pure returns (uint256) {
        return x - 0;
    }

    /// @dev Input: x in [0, 2^256-1], self subtraction always 0
    function test_sub_self(uint256 x) public pure returns (uint256) {
        return x - x;
    }

    // ============ Signed Subtraction ============

    /// @dev Signed: x - 1, underflow at min
    function test_sub_one_signed(int256 x) public pure returns (int256) {
        return x - 1;
    }

    /// @dev Signed: x - y
    function test_sub_two_vars_signed(int256 x, int256 y) public pure returns (int256) {
        return x - y;
    }

    /// @dev Signed: known values
    function test_sub_constants_signed() public pure returns (int256) {
        int256 a = 15;
        int256 b = 10;
        return a - b;
    }

    /// @dev Signed: subtracting negative (effectively adding)
    function test_sub_negative_constant(int256 x) public pure returns (int256) {
        return x - (-5);
    }

    /// @dev Signed: self subtraction always 0
    function test_sub_self_signed(int256 x) public pure returns (int256) {
        return x - x;
    }
}
