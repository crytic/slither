// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Multiplication Rounding Propagation
/// @dev Rule: A * B => rounding(A), rounding(B) - multiplication preserves both operands
contract Test_Multiplication {
    /// @dev Helper to create DOWN tagged value
    function divDown(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return numerator / denominator;
    }

    /// @dev Helper to create UP tagged value
    function divUp(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return (numerator + denominator - 1) / denominator;
    }

    /// @dev DOWN * NEUTRAL = DOWN
    function test_down_times_neutral(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 downValue = divDown(a, b);
        return downValue * c;
    }

    /// @dev NEUTRAL * DOWN = DOWN
    function test_neutral_times_down(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 downValue = divDown(b, c);
        return a * downValue;
    }

    /// @dev UP * NEUTRAL = UP
    function test_up_times_neutral(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 upValue = divUp(a, b);
        return upValue * c;
    }

    /// @dev NEUTRAL * UP = UP
    function test_neutral_times_up(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 upValue = divUp(b, c);
        return a * upValue;
    }

    /// @dev DOWN * DOWN = DOWN
    function test_down_times_down(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 down1 = divDown(a, b);
        uint256 down2 = divDown(c, d);
        return down1 * down2;
    }

    /// @dev UP * UP = UP
    function test_up_times_up(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 up1 = divUp(a, b);
        uint256 up2 = divUp(c, d);
        return up1 * up2;
    }

    /// @dev DOWN * UP = UNKNOWN (conflict)
    function test_down_times_up(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 downValue = divDown(a, b);
        uint256 upValue = divUp(c, d);
        return downValue * upValue;
    }
}
