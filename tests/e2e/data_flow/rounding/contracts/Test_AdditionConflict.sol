// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: UP + DOWN addition conflict → UNKNOWN + inconsistency
contract Test_AdditionConflict {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    function conflict(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 up = divUp(a, b);
        uint256 down = divDown(c, d);
        uint256 result = up + down;
        return result;
    }

    function preserves(uint256 a, uint256 b, uint256 z) external pure returns (uint256) {
        uint256 down = divDown(a, b);
        uint256 result = down + z;
        return result;
    }
}
