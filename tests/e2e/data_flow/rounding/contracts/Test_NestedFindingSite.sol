// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test_NestedFindingSite {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    // Both-DOWN division inconsistency lives HERE (depth 2 from entry)
    function conflicting(uint256 a, uint256 b, uint256 c, uint256 d) internal pure returns (uint256) {
        uint256 d1 = divDown(a, b);
        uint256 d2 = divDown(c, d);
        return d1 / d2;
    }

    // Middle frame (depth 1)
    function mid(uint256 a, uint256 b, uint256 c, uint256 d) internal pure returns (uint256) {
        uint256 m = conflicting(a, b, c, d);
        return m;
    }

    function entry(uint256 w, uint256 x, uint256 y, uint256 z) external pure returns (uint256) {
        uint256 result = mid(w, x, y, z);
        return result;
    }
}
