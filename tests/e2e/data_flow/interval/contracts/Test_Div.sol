// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Division Operations
/// @dev Tests interval analysis for div operations (unsigned and signed)
contract Test_Div {
    // ============ Unsigned Division ============

    /// @dev Input: x in [0, 2^256-1], Output: [0, 2^255-1]
    function test_div_two(uint256 x) public pure returns (uint256) {
        return x / 2;
    }

    /// @dev Input: x,y in [0, 2^256-1], y != 0
    function test_div_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
        return x / y;
    }

    /// @dev Input: known values, Output: exact result [2, 2]
    function test_div_constants() public pure returns (uint256) {
        uint256 a = 10;
        uint256 b = 5;
        return a / b;
    }

    /// @dev Division by one (identity)
    function test_div_one(uint256 x) public pure returns (uint256) {
        return x / 1;
    }

    /// @dev Self division: x / x = 1 (for x != 0)
    function test_div_self(uint256 x) public pure returns (uint256) {
        return x / x;
    }

    // ============ Signed Division ============

    /// @dev Signed: x / 2
    function test_div_two_signed(int256 x) public pure returns (int256) {
        return x / 2;
    }

    /// @dev Signed: x / y
    function test_div_two_vars_signed(int256 x, int256 y) public pure returns (int256) {
        return x / y;
    }

    /// @dev Signed: known values, Output: exact result [2, 2]
    function test_div_constants_signed() public pure returns (int256) {
        int256 a = 10;
        int256 b = 5;
        return a / b;
    }

    /// @dev Signed: dividing by negative
    function test_div_negative_constant(int256 x) public pure returns (int256) {
        return x / (-2);
    }

    /// @dev Signed: self division
    function test_div_self_signed(int256 x) public pure returns (int256) {
        return x / x;
    }
}
