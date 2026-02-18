// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

error ZeroValue();

/// @title Test: Revert Operations
/// @dev Tests interval analysis for revert call handling
contract Test_Revert {
    // ============ Basic revert ============

    /// @dev Plain revert after variable declaration; path is unreachable
    function test_revert_basic() public pure returns (uint256) {
        uint256 x = 42;
        revert();
        x += 3;
        return x;
    }

    /// @dev Revert with string message
    function test_revert_with_message() public pure returns (uint256) {
        uint256 x = 10;
        revert("always reverts");
        return x;
    }

    // ============ Custom error revert ============

    /// @dev Revert with custom error after variable declaration
    function test_revert_custom_error() public pure returns (uint256) {
        uint256 x = 99;
        revert ZeroValue();
        return x;
    }

    // ============ Conditional revert ============

    /// @dev Revert in one branch; the other branch should still be analyzed
    function test_revert_in_if(uint256 x) public pure returns (uint256) {
        if (x == 0) {
            revert("zero not allowed");
        }
        x += 23;
        return x;
    }
}
