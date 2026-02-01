// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Unary Operations
/// @dev Tests interval analysis for unary operations (!, ~)
contract Test_Unary {
    // ============ Logical Not (!) ============

    /// @dev Input: true, Output: false [0, 0]
    function test_not_true() public pure returns (bool) {
        bool a = true;
        return !a;
    }

    /// @dev Input: false, Output: true [1, 1]
    function test_not_false() public pure returns (bool) {
        bool a = false;
        return !a;
    }

    /// @dev Input: bool param, Output: inverted
    function test_not_param(bool x) public pure returns (bool) {
        return !x;
    }

    /// @dev Double negation: !!x = x
    function test_not_double(bool x) public pure returns (bool) {
        return !!x;
    }

    // ============ Bitwise Not (~) ============

    /// @dev Input: 0, Output: max uint256
    function test_tild_zero() public pure returns (uint256) {
        uint256 a = 0;
        return ~a;
    }

    /// @dev Input: max, Output: 0
    function test_tild_max() public pure returns (uint256) {
        uint256 a = type(uint256).max;
        return ~a;
    }

    /// @dev Input: known value, Output: ~10
    function test_tild_constant() public pure returns (uint256) {
        uint256 a = 10;
        return ~a;
    }

    /// @dev Input: uint256 param
    function test_tild_param(uint256 x) public pure returns (uint256) {
        return ~x;
    }

    /// @dev Double bitwise not: ~~x = x
    function test_tild_double(uint256 x) public pure returns (uint256) {
        return ~~x;
    }

    // ============ Signed Bitwise Not ============

    /// @dev Signed: ~0 = -1
    function test_tild_zero_signed() public pure returns (int256) {
        int256 a = 0;
        return ~a;
    }

    /// @dev Signed: ~(-1) = 0
    function test_tild_neg_one_signed() public pure returns (int256) {
        int256 a = -1;
        return ~a;
    }

    /// @dev Signed param
    function test_tild_param_signed(int256 x) public pure returns (int256) {
        return ~x;
    }
}
