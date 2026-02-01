// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Multiplication Operations
/// @dev Tests interval analysis for mul operations (unsigned and signed)
contract Test_Mul {
    // ============ Unsigned Multiplication ============

    /// @dev Input: x in [0, 2^256-1], overflow constrained
    function test_mul_two(uint256 x) public pure returns (uint256) {
        return x * 2;
    }

    /// @dev Input: x,y in [0, 2^256-1]
    function test_mul_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
        return x * y;
    }

    /// @dev Input: known values, Output: exact result [50, 50]
    function test_mul_constants() public pure returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        return a * b;
    }

    /// @dev Input: x in [0, 2^256-1], multiplying by zero always 0
    function test_mul_zero(uint256 x) public pure returns (uint256) {
        return x * 0;
    }

    /// @dev Input: x in [0, 2^256-1], multiplying by one (identity)
    function test_mul_one(uint256 x) public pure returns (uint256) {
        return x * 1;
    }

    /// @dev Squaring: x constrained to [0, 2^128-1]
    function test_mul_self(uint256 x) public pure returns (uint256) {
        return x * x;
    }

    // ============ Signed Multiplication ============

    /// @dev Signed: x * 2
    function test_mul_two_signed(int256 x) public pure returns (int256) {
        return x * 2;
    }

    /// @dev Signed: x * y
    function test_mul_two_vars_signed(int256 x, int256 y) public pure returns (int256) {
        return x * y;
    }

    /// @dev Signed: known values, Output: exact result [50, 50]
    function test_mul_constants_signed() public pure returns (int256) {
        int256 a = 5;
        int256 b = 10;
        return a * b;
    }

    /// @dev Signed: multiplying by negative
    function test_mul_negative_constant(int256 x) public pure returns (int256) {
        return x * (-2);
    }

    /// @dev Signed: squaring (result always non-negative)
    function test_mul_self_signed(int256 x) public pure returns (int256) {
        return x * x;
    }
}
