// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: recursive tuple-returning call must be a silent no-op
/// @dev The recursion guard inside `bounds` must NOT raise the
///      "analyzed body but found no return tags" RuntimeError; the
///      caller still gets per-index tags from the base-case return.
contract Test_TupleRecursion {
    function bounds(uint256 a, uint256 b) internal pure returns (uint256, uint256) {
        if (a == 0) {
            return (a / b, (a + b - 1) / b);
        }
        (uint256 lo, uint256 hi) = bounds(a - 1, b);
        return (lo, hi);
    }

    function caller(uint256 x, uint256 y) external pure returns (uint256, uint256) {
        (uint256 l, uint256 h) = bounds(x, y);
        return (l, h);
    }
}
