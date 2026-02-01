// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Require and Assert Operations
/// @dev Tests interval analysis for require/assert condition refinement
contract Test_RequireAssert {
    // ============ Require with comparisons ============

    /// @dev require(x > 0): x constrained to [1, max]
    function test_require_gt_zero(uint256 x) public pure returns (uint256) {
        require(x > 0);
        return x;
    }

    /// @dev require(x < 100): x constrained to [0, 99]
    function test_require_lt_constant(uint256 x) public pure returns (uint256) {
        require(x < 100);
        return x;
    }

    /// @dev require(x >= 10): x constrained to [10, max]
    function test_require_gte(uint256 x) public pure returns (uint256) {
        require(x >= 10);
        return x;
    }

    /// @dev require(x <= 50): x constrained to [0, 50]
    function test_require_lte(uint256 x) public pure returns (uint256) {
        require(x <= 50);
        return x;
    }

    /// @dev require(x == 42): x constrained to [42, 42]
    function test_require_eq(uint256 x) public pure returns (uint256) {
        require(x == 42);
        return x;
    }

    /// @dev require(x != 0): x constrained to [1, max] (nonzero)
    function test_require_neq_zero(uint256 x) public pure returns (uint256) {
        require(x != 0);
        return x;
    }

    // ============ Multiple requires (conjunction) ============

    /// @dev require(x > 10) && require(x < 20): x in [11, 19]
    function test_require_range(uint256 x) public pure returns (uint256) {
        require(x > 10);
        require(x < 20);
        return x;
    }

    /// @dev require(x >= 5) && require(x <= 10): x in [5, 10]
    function test_require_bounded(uint256 x) public pure returns (uint256) {
        require(x >= 5);
        require(x <= 10);
        return x;
    }

    // ============ Require with expressions ============

    /// @dev require(x + 1 > 5): x constrained to [5, max]
    function test_require_expr_add(uint256 x) public pure returns (uint256) {
        require(x + 1 > 5);
        return x;
    }

    /// @dev require(x * 2 < 100): x constrained to [0, 49]
    function test_require_expr_mul(uint256 x) public pure returns (uint256) {
        require(x * 2 < 100);
        return x;
    }

    // ============ Assert operations ============

    /// @dev assert(x > 0): same as require for analysis purposes
    function test_assert_gt_zero(uint256 x) public pure returns (uint256) {
        assert(x > 0);
        return x;
    }

    /// @dev assert(x < 100): x constrained to [0, 99]
    function test_assert_lt(uint256 x) public pure returns (uint256) {
        assert(x < 100);
        return x;
    }

    // ============ Signed comparisons ============

    /// @dev require(x > -10): signed x constrained to [-9, max_int]
    function test_require_signed_gt(int256 x) public pure returns (int256) {
        require(x > -10);
        return x;
    }

    /// @dev require(x < 0): signed x constrained to [min_int, -1]
    function test_require_signed_negative(int256 x) public pure returns (int256) {
        require(x < 0);
        return x;
    }

    /// @dev require(x >= -5) && require(x <= 5): x in [-5, 5]
    function test_require_signed_range(int256 x) public pure returns (int256) {
        require(x >= -5);
        require(x <= 5);
        return x;
    }

    // ============ Two variables ============

    /// @dev require(x < y): constrains relationship between x and y
    function test_require_two_vars(uint256 x, uint256 y) public pure returns (uint256) {
        require(x < y);
        return x + y;
    }

    /// @dev require(x == y): both must be equal
    function test_require_equal_vars(uint256 x, uint256 y) public pure returns (uint256) {
        require(x == y);
        return x;
    }

    // ============ Impossible/Unreachable paths ============

    /// @dev Impossible: x = 10, then require(x > 10) -> UNREACHABLE
    function test_impossible_gt(uint256 x) public pure returns (uint256) {
        x = 10;
        require(x > 10);
        return x;
    }

    /// @dev Impossible: x = 5, then require(x < 5) -> UNREACHABLE
    function test_impossible_lt(uint256 x) public pure returns (uint256) {
        x = 5;
        require(x < 5);
        return x;
    }

    /// @dev Impossible: x = 0, then require(x != 0) -> UNREACHABLE
    function test_impossible_neq(uint256 x) public pure returns (uint256) {
        x = 0;
        require(x != 0);
        return x;
    }

    /// @dev Impossible: x = 10, then assert(x == 5) -> UNREACHABLE
    function test_impossible_assert(uint256 x) public pure returns (uint256) {
        x = 10;
        assert(x == 5);
        return x;
    }

    /// @dev Impossible: contradictory requires -> UNREACHABLE
    function test_impossible_contradiction(uint256 x) public pure returns (uint256) {
        require(x > 100);
        require(x < 50);
        return x;
    }
}
