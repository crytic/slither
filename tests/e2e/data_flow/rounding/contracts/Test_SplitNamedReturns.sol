// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: named return values disagreeing in rounding direction
contract Test_SplitNamedReturns {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    /// One named return carries DOWN, the other UP → split-direction bug pattern
    function split(uint256 a, uint256 b) external pure returns (uint256 down, uint256 up) {
        down = divDown(a, b);
        up = divUp(a, b);
    }

    /// Both named returns carry DOWN → must NOT be flagged
    function aligned(uint256 a, uint256 b) external pure returns (uint256 first, uint256 second) {
        first = divDown(a, b);
        second = divDown(a, b + 1);
    }
}
