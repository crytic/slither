// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Engine fixture: diamond CFG merging conflicting tags
contract EngineDiamond {
    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function diamond(uint256 a, uint256 b, bool flag) public pure returns (uint256) {
        uint256 r;
        if (flag) {
            r = divUp(a, b);
        } else {
            r = divDown(a, b);
        }
        return r;
    }
}
