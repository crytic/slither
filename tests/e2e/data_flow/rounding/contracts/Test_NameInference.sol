// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Name-Based Rounding Inference
/// @dev Tests that function names with down/floor/up/ceil patterns are recognized
contract Test_NameInference {
    /// @dev divDown should return DOWN tag
    function divDown(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return numerator / denominator;
    }

    /// @dev mulDown should return DOWN tag
    function mulDown(uint256 value, uint256 multiplier, uint256 divisor) internal pure returns (uint256) {
        return (value * multiplier) / divisor;
    }

    /// @dev roundFloor should return DOWN tag
    function roundFloor(uint256 value, uint256 precision) internal pure returns (uint256) {
        return (value / precision) * precision;
    }

    /// @dev divUp should return UP tag
    function divUp(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return (numerator + denominator - 1) / denominator;
    }

    /// @dev mulUp should return UP tag
    function mulUp(uint256 value, uint256 multiplier, uint256 divisor) internal pure returns (uint256) {
        return (value * multiplier + divisor - 1) / divisor;
    }

    /// @dev roundCeil should return UP tag
    function roundCeil(uint256 value, uint256 precision) internal pure returns (uint256) {
        return ((value + precision - 1) / precision) * precision;
    }

    /// @dev Caller using divDown - result should be DOWN
    function test_divDown_caller(uint256 amount, uint256 rate) external pure returns (uint256) {
        return divDown(amount, rate);
    }

    /// @dev Caller using mulDown - result should be DOWN
    function test_mulDown_caller(uint256 amount, uint256 rate, uint256 base) external pure returns (uint256) {
        return mulDown(amount, rate, base);
    }

    /// @dev Caller using roundFloor - result should be DOWN
    function test_roundFloor_caller(uint256 value, uint256 step) external pure returns (uint256) {
        return roundFloor(value, step);
    }

    /// @dev Caller using divUp - result should be UP
    function test_divUp_caller(uint256 amount, uint256 rate) external pure returns (uint256) {
        return divUp(amount, rate);
    }

    /// @dev Caller using mulUp - result should be UP
    function test_mulUp_caller(uint256 amount, uint256 rate, uint256 base) external pure returns (uint256) {
        return mulUp(amount, rate, base);
    }

    /// @dev Caller using roundCeil - result should be UP
    function test_roundCeil_caller(uint256 value, uint256 step) external pure returns (uint256) {
        return roundCeil(value, step);
    }
}
