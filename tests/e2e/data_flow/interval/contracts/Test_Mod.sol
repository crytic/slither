// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Modulo Operations
/// @dev Tests interval analysis for mod operations (unsigned and signed)
contract Test_Mod {
    // ============ Unsigned Modulo ============

    /// @dev Input: x in [0, 2^256-1], Output: [0, 1]
    function test_mod_two(uint256 x) public pure returns (uint256) {
        return x % 2;
    }

    /// @dev Input: x,y in [0, 2^256-1], y != 0, Output: [0, y-1]
    function test_mod_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
        return x % y;
    }

    /// @dev Input: known values, Output: exact result [0, 0]
    function test_mod_constants() public pure returns (uint256) {
        uint256 a = 10;
        uint256 b = 5;
        return a % b;
    }

    /// @dev Modulo by one always 0
    function test_mod_one(uint256 x) public pure returns (uint256) {
        return x % 1;
    }

    /// @dev Self modulo: x % x = 0 (for x != 0)
    function test_mod_self(uint256 x) public pure returns (uint256) {
        return x % x;
    }

    // ============ Signed Modulo ============

    /// @dev Signed: x % 2
    function test_mod_two_signed(int256 x) public pure returns (int256) {
        return x % 2;
    }

    /// @dev Signed: x % y
    function test_mod_two_vars_signed(int256 x, int256 y) public pure returns (int256) {
        return x % y;
    }

    /// @dev Signed: known values, Output: exact result [0, 0]
    function test_mod_constants_signed() public pure returns (int256) {
        int256 a = 10;
        int256 b = 5;
        return a % b;
    }

    /// @dev Signed: modulo by negative
    function test_mod_negative_constant(int256 x) public pure returns (int256) {
        return x % (-3);
    }

    /// @dev Signed: self modulo
    function test_mod_self_signed(int256 x) public pure returns (int256) {
        return x % x;
    }
}
