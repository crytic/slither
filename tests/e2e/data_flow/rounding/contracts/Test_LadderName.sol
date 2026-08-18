// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: name allowlist outranks body analysis
contract Test_LadderName {
    /// Name says UP; body floor-divides (body analysis would say DOWN)
    function mulUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function caller(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result = mulUp(a, b);
        return result;
    }
}
