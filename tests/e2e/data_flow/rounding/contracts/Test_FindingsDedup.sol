// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: finding dedup keys on (message, line)
/// @dev `conflicting` contains a DOWN/DOWN division inconsistency. Findings
///      from callee bodies are attributed to the caller's call-site line, so
///      two calls on one line dedup to one finding while two calls on
///      separate lines report twice.
contract Test_FindingsDedup {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function conflicting(uint256 a, uint256 b, uint256 c, uint256 d) internal pure returns (uint256) {
        uint256 d1 = divDown(a, b);
        uint256 d2 = divDown(c, d);
        return d1 / d2;
    }

    function sameLine(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 r1 = conflicting(a, b, c, d); uint256 r2 = conflicting(d, c, b, a);
        return r1 + r2;
    }

    function twoLines(uint256 a, uint256 b, uint256 c, uint256 d) external pure returns (uint256) {
        uint256 r1 = conflicting(a, b, c, d);
        uint256 r2 = conflicting(d, c, b, a);
        return r1 + r2;
    }
}
