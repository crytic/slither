// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: subtraction inverts the subtrahend's direction
contract Test_SubtractionInversion {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    /// NEUTRAL - DOWN: subtrahend inverts to UP, result UP
    function neutralMinusDown(uint256 a, uint256 b, uint256 z) external pure returns (uint256) {
        uint256 down = divDown(a, b);
        uint256 result = z - down;
        return result;
    }

    /// DOWN - UP: subtrahend inverts to DOWN, agrees with minuend, result DOWN
    function downMinusUp(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 down = divDown(a, b);
        uint256 up = divUp(c, d);
        uint256 result = down - up;
        return result;
    }

    /// DOWN - DOWN: subtrahend inverts to UP, conflicts with minuend → UNKNOWN
    function downMinusDown(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 down1 = divDown(a, b);
        uint256 down2 = divDown(c, d);
        uint256 result = down1 - down2;
        return result;
    }
}
