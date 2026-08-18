// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: three-value tuple return with per-index Unpack matching
contract Test_TupleThree {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    function three(uint256 a, uint256 b) internal pure returns (uint256, uint256, uint256) {
        uint256 lo = divDown(a, b);
        uint256 mid = a;
        uint256 hi = divUp(a, b);
        return (lo, mid, hi);
    }

    /// All three positions destructured: l → DOWN, m → NEUTRAL, h → UP
    function destructureAll(uint256 x, uint256 y) external pure returns (uint256) {
        (uint256 l, uint256 m, uint256 h) = three(x, y);
        return l + m + h;
    }

    /// Middle position skipped: index matching must still map 0 → l, 2 → h
    function skipMiddle(uint256 x, uint256 y) external pure returns (uint256) {
        (uint256 l, , uint256 h) = three(x, y);
        return l + h;
    }
}
