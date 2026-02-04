// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Division Rounding
/// @dev Tests rounding direction tracking for division operations
contract Test_Division {
    /// @dev Floor division: a / b rounds DOWN when denominator is neutral
    /// Expected: result tagged DOWN
    function test_floor_division(uint256 numerator, uint256 denominator)
        public
        pure
        returns (uint256)
    {
        return numerator / denominator;
    }

    /// @dev Ceiling division pattern: (a + b - 1) / b rounds UP
    /// Expected: result tagged UP
    function test_ceiling_division(uint256 numerator, uint256 denominator)
        public
        pure
        returns (uint256)
    {
        return (numerator + denominator - 1) / denominator;
    }

    /// @dev Simple assignment propagates rounding tag
    /// Expected: result tagged DOWN (from floor division)
    function test_assignment_propagation(uint256 numerator, uint256 denominator)
        public
        pure
        returns (uint256)
    {
        uint256 floored = numerator / denominator;
        uint256 result = floored;
        return result;
    }

    /// @dev Addition preserves rounding tag from non-neutral operand
    /// Expected: result tagged DOWN (from floor division)
    function test_addition_preserves_tag(uint256 numerator, uint256 denominator)
        public
        pure
        returns (uint256)
    {
        uint256 floored = numerator / denominator;
        return floored + 1;
    }

    /// @dev Multiplication preserves rounding tag from non-neutral operand
    /// Expected: result tagged DOWN (from floor division)
    function test_multiplication_preserves_tag(uint256 numerator, uint256 denominator)
        public
        pure
        returns (uint256)
    {
        uint256 floored = numerator / denominator;
        return floored * 2;
    }

    /// @dev Subtraction inverts rounding tag of subtrahend
    /// Expected: result tagged UP (inverted from DOWN)
    function test_subtraction_inverts_tag(uint256 numerator, uint256 denominator)
        public
        pure
        returns (uint256)
    {
        uint256 floored = numerator / denominator;
        return 100 - floored;
    }

    /// @dev Division by floor-rounded value inverts the tag
    /// Expected: result tagged UP (inverted from DOWN denominator)
    function test_division_inverts_denominator_tag(
        uint256 numerator,
        uint256 denominator,
        uint256 dividend
    )
        public
        pure
        returns (uint256)
    {
        uint256 floored = numerator / denominator;
        return dividend / floored;
    }
}
