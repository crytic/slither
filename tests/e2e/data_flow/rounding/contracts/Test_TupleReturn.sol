// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Tuple Return Handling
/// @dev Tests that rounding tags survive tuple returns and Unpack.
contract Test_TupleReturn {

    function divDown(
        uint256 numerator,
        uint256 denominator
    ) internal pure returns (uint256) {
        return numerator / denominator;
    }

    function divUp(
        uint256 numerator,
        uint256 denominator
    ) internal pure returns (uint256) {
        return (numerator + denominator - 1) / denominator;
    }

    /// @dev Returns (DOWN, UP) via named helpers.
    function divBoth(
        uint256 numerator,
        uint256 denominator
    ) internal pure returns (uint256 down, uint256 up) {
        down = divDown(numerator, denominator);
        up = divUp(numerator, denominator);
    }

    /// @dev Destructure (DOWN, UP) tuple.
    ///      Expected: floorResult → DOWN, ceilResult → UP
    function testBasicDestructure(
        uint256 x,
        uint256 y
    ) external pure returns (uint256 , uint256 ) {
        uint floorResult;
        uint ceilResult;
        (floorResult, ceilResult) = divBoth(x, y);
    }
}
