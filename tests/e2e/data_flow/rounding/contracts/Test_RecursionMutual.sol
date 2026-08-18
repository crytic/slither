// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: mutual recursion (a → b → a) must hit the guard
contract Test_RecursionMutual {
    function a(uint256 x) public pure returns (uint256) {
        if (x == 0) {
            return 1;
        }
        uint256 result = b(x - 1);
        return result;
    }

    function b(uint256 x) public pure returns (uint256) {
        uint256 result = a(x);
        return result;
    }
}
