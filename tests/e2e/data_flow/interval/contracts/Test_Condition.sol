// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Condition Operations
/// @dev Tests interval analysis for conditional branching (if/else).
/// @dev Conditions can narrow variable ranges on each branch.

contract Test_Condition {
    // ============ Simple conditions ============

    /// @dev Simple if with constant comparison
    /// @dev In true branch: x ∈ [0, 9], in false branch: x ∈ [10, max]
    function test_if_less_than(uint256 x) public pure returns (uint256) {
        if (x < 10) {
            return x + 1;  // x narrowed to [0, 9]
        }
        return x;  // x narrowed to [10, max]
    }

    /// @dev Simple if with greater than
    /// @dev In true branch: x ∈ [100, max], in false branch: x ∈ [0, 99]
    function test_if_greater_than(uint256 x) public pure returns (uint256) {
        if (x > 99) {
            return x - 50;  // x narrowed to [100, max]
        }
        return x + 50;  // x narrowed to [0, 99]
    }

    /// @dev Equality check
    /// @dev In true branch: x == 42
    function test_if_equal(uint256 x) public pure returns (uint256) {
        if (x == 42) {
            return 100;  // x narrowed to [42, 42]
        }
        return x;  // x != 42
    }

    /// @dev Not equal check
    function test_if_not_equal(uint256 x) public pure returns (uint256) {
        if (x != 0) {
            return x * 2;  // x narrowed to [1, max]
        }
        return 1;  // x == 0
    }

    // // ============ Signed conditions ============

    // /// @dev Signed comparison
    // /// @dev In true branch: x ∈ [-max, -1]
    // function test_if_signed_negative(int256 x) public pure returns (int256) {
    //     if (x < 0) {
    //         return -x;  // x narrowed to negative range
    //     }
    //     return x;  // x narrowed to [0, max]
    // }

    // /// @dev Signed greater than zero
    // function test_if_signed_positive(int256 x) public pure returns (int256) {
    //     if (x > 0) {
    //         return x - 1;  // x narrowed to [1, max]
    //     }
    //     return x + 1;  // x narrowed to [-max, 0]
    // }

    // // ============ Compound conditions ============

    // /// @dev Range check with two conditions
    // /// @dev After both checks: x ∈ [10, 99]
    // function test_range_check(uint256 x) public pure returns (uint256) {
    //     if (x >= 10) {
    //         if (x < 100) {
    //             return x * 2;  // x narrowed to [10, 99]
    //         }
    //     }
    //     return 0;
    // }

    // /// @dev Early return pattern
    // /// @dev After guard: x ∈ [1, max]
    // function test_early_return(uint256 x) public pure returns (uint256) {
    //     if (x == 0) {
    //         return 0;
    //     }
    //     // x != 0 here, so x ∈ [1, max]
    //     return 100 / x;
    // }

    // // ============ Conditions with arithmetic ============

    // /// @dev Condition result used in arithmetic
    // function test_condition_with_arithmetic(uint256 x) public pure returns (uint256) {
    //     uint256 result;
    //     if (x < 50) {
    //         result = x + 10;  // x ∈ [0, 49], result ∈ [10, 59]
    //     } else {
    //         result = x - 10;  // x ∈ [50, max], result ∈ [40, max-10]
    //     }
    //     return result;
    // }

    // /// @dev Multiple variables in condition
    // function test_two_variables(uint256 x, uint256 y) public pure returns (uint256) {
    //     if (x < y) {
    //         return y - x;  // guaranteed positive since x < y
    //     }
    //     return x - y;  // x >= y, so x - y >= 0
    // }

    // // ============ Boolean conditions ============

    // /// @dev Boolean parameter as condition
    // function test_bool_condition(bool flag, uint256 x) public pure returns (uint256) {
    //     if (flag) {
    //         return x + 1;
    //     }
    //     return x;
    // }

    // /// @dev Negated condition
    // function test_negated_condition(uint256 x) public pure returns (uint256) {
    //     if (!(x > 100)) {
    //         return x + 50;  // x ∈ [0, 100]
    //     }
    //     return x - 50;  // x ∈ [101, max]
    // }

    // // ============ Ternary operator ============

    // /// @dev Ternary with comparison
    // function test_ternary(uint256 x) public pure returns (uint256) {
    //     return x < 10 ? x + 1 : x - 1;
    // }

    // /// @dev Nested ternary
    // function test_nested_ternary(uint256 x) public pure returns (uint256) {
    //     return x < 10 ? 0 : (x < 100 ? 1 : 2);
    // }
}
