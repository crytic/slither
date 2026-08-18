// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: direct recursion must hit the guard, not loop forever
contract Test_RecursionDirect {
    function rec(uint256 x) public pure returns (uint256) {
        if (x == 0) {
            return 1;
        }
        uint256 result = rec(x - 1);
        return result;
    }
}
