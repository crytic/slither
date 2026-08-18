// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: variable-name suffix annotations vs. inferred direction
contract Test_AnnotationMismatch {
    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    /// Suffix claims DOWN, inference says UP → mismatch finding
    function mismatch(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result_DOWN = divUp(a, b);
        return result_DOWN;
    }

    /// Suffix matches the inferred UP → no finding
    function matching(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result_UP = divUp(a, b);
        return result_UP;
    }
}
