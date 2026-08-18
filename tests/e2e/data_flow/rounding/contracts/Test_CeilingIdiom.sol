// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: ceiling-division idiom detection and near-misses
contract Test_CeilingIdiom {
    /// Canonical (a + b - 1) / b → UP
    function ceiling(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result = (a + b - 1) / b;
        return result;
    }

    /// Constant is 2, not 1 → plain floor division, DOWN
    function nearMissConstant(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result = (a + b - 2) / b;
        return result;
    }

    /// Divisor is not an addend of the dividend → plain floor division, DOWN
    function nearMissDivisor(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 result = (a + b - 1) / c;
        return result;
    }
}
