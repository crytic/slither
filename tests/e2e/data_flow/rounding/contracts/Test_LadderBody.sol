// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: fallthrough to full body analysis
/// @dev Neutral name, no annotation, no known-library entry: only walking
///      the body reveals the floor division → DOWN.
contract Test_LadderBody {
    function compute(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function caller(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result = compute(a, b);
        return result;
    }
}
