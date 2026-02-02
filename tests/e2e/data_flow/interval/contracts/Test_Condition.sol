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
}
