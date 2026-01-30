// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Addition Operations
/// @dev Tests interval analysis for add operations
contract Test_Add {
    /// @dev Input: x in [0, 2^256-1], Output: [1, 2^256] (may overflow)
    function test_add_one(uint256 x) public pure returns (uint256) {
        return x + 1;
    }

    /// @dev Input: x,y in [0, 2^256-1], Output: [0, 2^256] (may overflow)
    function test_add_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
        return x + y;
    }

    /// @dev Input: known values, Output: exact result [15, 15]
    function test_add_constants() public pure returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        return a + b;
    }

    /// @dev Input: x in [0, 2^256-1], edge case max value
    function test_add_max(uint256 x) public pure returns (uint256) {
        return x + type(uint256).max;
    }

    /// @dev Input: x in [0, 2^256-1], adding zero (identity)
    function test_add_zero(uint256 x) public pure returns (uint256) {
        return x + 0;
    }
}
