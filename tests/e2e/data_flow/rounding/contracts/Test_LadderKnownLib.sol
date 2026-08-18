// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: known-library table outranks body analysis
/// @dev FullMath.mulDiv is DOWN in the builtin table, but the body here is a
///      ceiling division (body analysis would say UP). With the table loaded
///      the table must win; without it, body analysis must find UP.
library FullMath {
    function mulDiv(uint256 a, uint256 b, uint256 d) internal pure returns (uint256) {
        return (a * b + d - 1) / d;
    }
}

contract Test_LadderKnownLib {
    function caller(uint256 x, uint256 y, uint256 d) external pure returns (uint256) {
        uint256 result = FullMath.mulDiv(x, y, d);
        return result;
    }
}
