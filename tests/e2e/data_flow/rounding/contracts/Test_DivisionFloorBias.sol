// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: division floor bias when either operand is NEUTRAL
contract Test_DivisionFloorBias {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    /// UP / NEUTRAL: floor bias overrides the numerator's UP → DOWN
    function upDivNeutral(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 up = divUp(a, b);
        uint256 result = up / c;
        return result;
    }

    /// NEUTRAL / DOWN: floor bias overrides the inverted denominator's UP → DOWN
    function neutralDivDown(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 down = divDown(b, c);
        uint256 result = a / down;
        return result;
    }

    /// UP / DOWN: no NEUTRAL operand, signals agree after inversion → UP
    function upDivDown(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 up = divUp(a, b);
        uint256 down = divDown(c, d);
        uint256 result = up / down;
        return result;
    }
}
