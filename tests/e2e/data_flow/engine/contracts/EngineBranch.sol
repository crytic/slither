// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Branch shapes for the cfg_utils branch-condition helpers
contract EngineBranch {
    function pick(uint256 amount, bool roundUp) public pure returns (uint256) {
        uint256 result = amount;
        if (roundUp) {
            result = result + 1;
            result = result + 2;
        } else {
            result = result - 1;
            result = result - 2;
        }
        return result;
    }

    function straight(uint256 amount) public pure returns (uint256) {
        uint256 result = amount + 1;
        return result;
    }
}
