// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Comparison Operations
/// @dev Tests interval analysis for comparisons (without control flow)
contract Test_Comparison {
    // ============ Equal (==) ============

    /// @dev Constants: 5 == 5 -> true [1, 1]
    function test_eq_true() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 5;
        return a == b;
    }

    /// @dev Constants: 5 == 10 -> false [0, 0]
    function test_eq_false() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 10;
        return a == b;
    }

    /// @dev Variables: x == y -> [0, 1]
    function test_eq_vars(uint256 x, uint256 y) public pure returns (bool) {
        return x == y;
    }

    /// @dev Zero check: x == 0 -> [0, 1]
    function test_eq_zero(uint256 x) public pure returns (bool) {
        return x == 0;
    }

    // ============ Not Equal (!=) ============

    /// @dev Constants: 5 != 10 -> true [1, 1]
    function test_neq_true() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 10;
        return a != b;
    }

    /// @dev Constants: 5 != 5 -> false [0, 0]
    function test_neq_false() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 5;
        return a != b;
    }

    /// @dev Variables: x != y -> [0, 1]
    function test_neq_vars(uint256 x, uint256 y) public pure returns (bool) {
        return x != y;
    }

    // ============ Less Than (<) ============

    /// @dev Constants: 5 < 10 -> true [1, 1]
    function test_lt_true() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 10;
        return a < b;
    }

    /// @dev Constants: 10 < 5 -> false [0, 0]
    function test_lt_false() public pure returns (bool) {
        uint256 a = 10;
        uint256 b = 5;
        return a < b;
    }

    /// @dev Variables: x < y -> [0, 1]
    function test_lt_vars(uint256 x, uint256 y) public pure returns (bool) {
        return x < y;
    }

    // ============ Greater Than (>) ============

    /// @dev Constants: 10 > 5 -> true [1, 1]
    function test_gt_true() public pure returns (bool) {
        uint256 a = 10;
        uint256 b = 5;
        return a > b;
    }

    /// @dev Constants: 5 > 10 -> false [0, 0]
    function test_gt_false() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 10;
        return a > b;
    }

    /// @dev Variables: x > y -> [0, 1]
    function test_gt_vars(uint256 x, uint256 y) public pure returns (bool) {
        return x > y;
    }

    // ============ Less Than or Equal (<=) ============

    /// @dev Constants: 5 <= 5 -> true [1, 1]
    function test_lte_equal() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 5;
        return a <= b;
    }

    /// @dev Constants: 5 <= 10 -> true [1, 1]
    function test_lte_less() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 10;
        return a <= b;
    }

    /// @dev Variables: x <= y -> [0, 1]
    function test_lte_vars(uint256 x, uint256 y) public pure returns (bool) {
        return x <= y;
    }

    // ============ Greater Than or Equal (>=) ============

    /// @dev Constants: 5 >= 5 -> true [1, 1]
    function test_gte_equal() public pure returns (bool) {
        uint256 a = 5;
        uint256 b = 5;
        return a >= b;
    }

    /// @dev Constants: 10 >= 5 -> true [1, 1]
    function test_gte_greater() public pure returns (bool) {
        uint256 a = 10;
        uint256 b = 5;
        return a >= b;
    }

    /// @dev Variables: x >= y -> [0, 1]
    function test_gte_vars(uint256 x, uint256 y) public pure returns (bool) {
        return x >= y;
    }

    // ============ Signed Comparisons ============

    /// @dev Signed: -5 < 5 -> true [1, 1]
    function test_lt_signed() public pure returns (bool) {
        int256 a = -5;
        int256 b = 5;
        return a < b;
    }

    /// @dev Signed: -5 > 5 -> false [0, 0]
    function test_gt_signed() public pure returns (bool) {
        int256 a = -5;
        int256 b = 5;
        return a > b;
    }

    /// @dev Signed variables: x < y -> [0, 1]
    function test_lt_signed_vars(int256 x, int256 y) public pure returns (bool) {
        return x < y;
    }
}
