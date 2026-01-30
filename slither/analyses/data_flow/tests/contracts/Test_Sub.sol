// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Subtraction Operations
/// @dev Tests interval analysis for sub operations
contract Test_Sub {
    /// @dev Input: x in [0, 2^256-1], Output: underflow possible
    function test_sub_one(uint256 x) public pure returns (uint256) {
        return x - 1;
    }

    /// @dev Input: x,y in [0, 2^256-1], Output: underflow possible
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
}
