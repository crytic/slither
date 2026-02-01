// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Addition Operations
/// @dev Tests interval analysis for add operations (unsigned and signed)
contract Test_Add {
    // ============ Unsigned Addition ============

    /// @dev Input: x in [0, 2^256-1], Output: overflow constrained
    function test_add_one(uint256 x) public pure returns (uint256) {
        return x + 1;
    }

    /// @dev Input: x,y in [0, 2^256-1]
    function test_add_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
        return x + y;
    }

    /// @dev Input: known values, Output: exact result [15, 15]
    function test_add_constants() public pure returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        return a + b;
    }

    /// @dev Input: x in [0, 2^256-1], adding zero (identity)
    function test_add_zero(uint256 x) public pure returns (uint256) {
        return x + 0;
    }

    // ============ Signed Addition ============

    /// @dev Signed: x + 1, overflow at max
    function test_add_one_signed(int256 x) public pure returns (int256) {
        return x + 1;
    }

    /// @dev Signed: x + y
    function test_add_two_vars_signed(int256 x, int256 y) public pure returns (int256) {
        return x + y;
    }

    /// @dev Signed: known values, Output: exact result [15, 15]
    function test_add_constants_signed() public pure returns (int256) {
        int256 a = 5;
        int256 b = 10;
        return a + b;
    }

    /// @dev Signed: negative constant
    function test_add_negative_constant(int256 x) public pure returns (int256) {
        return x + (-5);
    }
}
