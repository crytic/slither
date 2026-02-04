// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Conditional Rounding Based on Flag
/// @dev Tests rounding direction when controlled by a boolean flag argument.
contract Test_ConditionalRounding {
    /// @dev Floor division (rounds down)
    function divDown(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return numerator / denominator;
    }

    /// @dev Ceiling division (rounds up)
    function divUp(uint256 numerator, uint256 denominator) internal pure returns (uint256) {
        return (numerator + denominator - 1) / denominator;
    }

    function foo (uint a, uint b) public pure returns (uint256) {
        return divDown(a, b);
    }

    /// @dev Returns UP when roundUp=true, DOWN when roundUp=false
    function computeWithRounding(
        uint256 value,
        uint256 divisor,
        bool roundUp
    ) public pure returns (uint256) {
        if (roundUp) {
            return divUp(value, divisor);
        } else {
            return foo(value, divisor);
        }
    }

    /// @dev Calls computeWithRounding - tests interprocedural rounding propagation
    function computeViaCall(
        uint256 value,
        uint256 divisor,
        bool roundUp
    ) external pure returns (uint256) {
        return computeWithRounding(value, divisor, roundUp);
    }
}
