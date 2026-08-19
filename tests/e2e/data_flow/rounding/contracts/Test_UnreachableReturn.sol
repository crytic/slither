// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test_UnreachableReturn {
    // The second return is unreachable: its Return node is never visited
    // by the callee fixpoint, so the summary reads it from bottom state.
    function helper(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
        return b;
    }

    function caller(uint256 x, uint256 y) external pure returns (uint256) {
        uint256 result = helper(x, y);
        return result;
    }
}
