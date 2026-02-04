// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Division Rounding Propagation
/// @dev Rule: A / B => rounding(A), !rounding(B), floor default when NEUTRAL
/// Denominator tag is inverted. Same non-NEUTRAL tags = inconsistency.
contract Test_Division {
    /// @dev Helper to create DOWN tagged value
    function divDown(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return numerator / denominator;
    }

    /// @dev Helper to create UP tagged value
    function divUp(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return (numerator + denominator - 1) / denominator;
    }

    /// @dev NEUTRAL / NEUTRAL = DOWN (floor division default)
    function test_neutral_div_neutral(uint256 a, uint256 b) external pure returns (uint256) {
        return a / b;
    }

    /// @dev DOWN / NEUTRAL = DOWN
    function test_down_div_neutral(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 downValue = divDown(a, b);
        return downValue / c;
    }

    /// @dev UP / NEUTRAL = UP
    function test_up_div_neutral(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 upValue = divUp(a, b);
        return upValue / c;
    }

    /// @dev NEUTRAL / DOWN = UP (DOWN inverted to UP)
    function test_neutral_div_down(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 downValue = divDown(b, c);
        return a / downValue;
    }

    /// @dev NEUTRAL / UP = DOWN (UP inverted to DOWN)
    function test_neutral_div_up(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 upValue = divUp(b, c);
        return a / upValue;
    }

    /// @dev DOWN / UP = DOWN (UP inverted to DOWN, combines with DOWN)
    function test_down_div_up(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 downValue = divDown(a, b);
        uint256 upValue = divUp(c, d);
        return downValue / upValue;
    }

    /// @dev UP / DOWN = UP (DOWN inverted to UP, combines with UP)
    function test_up_div_down(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 upValue = divUp(a, b);
        uint256 downValue = divDown(c, d);
        return upValue / downValue;
    }

    /// @dev DOWN / DOWN = UNKNOWN (inconsistency: same non-NEUTRAL tags)
    function test_down_div_down(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 down1 = divDown(a, b);
        uint256 down2 = divDown(c, d);
        return down1 / down2;
    }

    /// @dev UP / UP = UNKNOWN (inconsistency: same non-NEUTRAL tags)
    function test_up_div_up(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 up1 = divUp(a, b);
        uint256 up2 = divUp(c, d);
        return up1 / up2;
    }
}
