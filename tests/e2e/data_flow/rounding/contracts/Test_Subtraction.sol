// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Subtraction Rounding Propagation
/// @dev Rule: A - B => rounding(A), !rounding(B) - right operand is inverted
contract Test_Subtraction {
    /// @dev Helper to create DOWN tagged value
    function divDown(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return numerator / denominator;
    }

    /// @dev Helper to create UP tagged value
    function divUp(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return (numerator + denominator - 1) / denominator;
    }

    /// @dev DOWN - NEUTRAL = DOWN (NEUTRAL inverted is still NEUTRAL)
    function test_down_minus_neutral(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 downValue = divDown(a, b);
        return downValue - c;
    }

    /// @dev NEUTRAL - DOWN = UP (DOWN inverted to UP)
    function test_neutral_minus_down(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 downValue = divDown(b, c);
        return a - downValue;
    }

    /// @dev UP - NEUTRAL = UP (NEUTRAL inverted is still NEUTRAL)
    function test_up_minus_neutral(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 upValue = divUp(a, b);
        return upValue - c;
    }

    /// @dev NEUTRAL - UP = DOWN (UP inverted to DOWN)
    function test_neutral_minus_up(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 upValue = divUp(b, c);
        return a - upValue;
    }

    /// @dev DOWN - DOWN = UNKNOWN (DOWN + UP conflict after inversion)
    function test_down_minus_down(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 down1 = divDown(a, b);
        uint256 down2 = divDown(c, d);
        return down1 - down2;
    }

    /// @dev UP - UP = UNKNOWN (UP + DOWN conflict after inversion)
    function test_up_minus_up(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 up1 = divUp(a, b);
        uint256 up2 = divUp(c, d);
        return up1 - up2;
    }

    /// @dev DOWN - UP = DOWN (DOWN + DOWN after UP inverted to DOWN)
    function test_down_minus_up(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 downValue = divDown(a, b);
        uint256 upValue = divUp(c, d);
        return downValue - upValue;
    }

    /// @dev UP - DOWN = UP (UP + UP after DOWN inverted to UP)
    function test_up_minus_down(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 upValue = divUp(a, b);
        uint256 downValue = divDown(c, d);
        return upValue - downValue;
    }
}
