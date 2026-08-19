// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test_MultiTagArgument {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    // Split-return callee: summary tags = {DOWN, UP}
    function conditional(uint256 a, uint256 b, bool up) internal pure returns (uint256) {
        if (up) {
            return divUp(a, b);
        }
        return divDown(a, b);
    }

    function passthrough(uint256 v) internal pure returns (uint256) {
        return v;
    }

    function twoStep(uint256 x, uint256 y, bool up) external pure returns (uint256) {
        uint256 v = conditional(x, y, up);
        uint256 result = passthrough(v);
        return result;
    }
}
