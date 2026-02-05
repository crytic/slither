// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Interprocedural Tag Propagation
/// @dev Tests that rounding tags propagate correctly through function calls.
contract Test_Interprocedural {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    /// @dev Helper that multiplies a value - tag comes from parameter
    function scale(uint256 value, uint256 factor) internal pure returns (uint256) {
        return value * factor;
    }

    /// @dev Helper that adds two values - tags come from parameters
    function combine(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    /// @dev Test: DOWN tag propagates through helper
    function testPassDown(uint256 x, uint256 y) external pure returns (uint256) {
        uint256 result = divDown(x, y);
        return scale(result, 2);
    }

    /// @dev Test: UP tag propagates through helper
    function testPassUp(uint256 x, uint256 y) external pure returns (uint256) {
        uint256 result = divUp(x, y);
        return scale(result, 2);
    }

    /// @dev Test: Two DOWN values combine correctly
    function testCombineSame(uint256 x, uint256 y) external pure returns (uint256) {
        uint256 a = divDown(x, y);
        uint256 b = divDown(x, y + 1);
        return combine(a, b);
    }

    /// @dev Test: Nested calls preserve context
    function wrapper(uint256 value) internal pure returns (uint256) {
        return scale(value, 3);
    }

    function testNested(uint256 x, uint256 y) external pure returns (uint256) {
        uint256 result = divDown(x, y);
        return wrapper(result);
    }
}
