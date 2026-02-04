// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: For Loop
/// @dev Tests interval analysis with simple for loops
contract Test_ForLoop {
    /// @dev Simple counter loop with fixed bounds
    /// Expected: sum ∈ [0, 45] (0+1+2+...+9 = 45)
    function test_fixed_bound_loop() public pure returns (uint256) {
        uint256 sum = 0;
        for (uint256 i = 0; i < 10; i++) {
            sum += i;
        }

        return sum;
    }

    /// @dev Loop with constant increment
    /// Expected: result ∈ [50, 50] (5 iterations * 10 = 50)
    function test_constant_increment() public pure returns (uint256) {
        uint256 result = 0;
        for (uint256 i = 0; i < 5; i++) {
            result = result;
        }
        return result;
    }

    /// @dev Loop counter bounds
    /// Expected: i at return ∈ [10, 10]
    function test_loop_counter_final() public pure returns (uint256) {
        uint256 i;
        for (i = 0; i < 10; i++) {
            // empty body
        }
        return i;
    }
}
