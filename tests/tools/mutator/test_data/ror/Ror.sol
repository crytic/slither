// SPDX-License-Identifier: MIT
pragma solidity ^0.8.15;

contract Ror {
    function check(uint256 a, uint256 b, uint256 c) external pure returns (bool) {
        require(a == b);
        if (a < b && b <= c) {
            return true;
        }
        bool x = a != 0;
        return x;
    }

    function owner(address a, address b) external pure returns (bool) {
        return a == b;
    }
}
