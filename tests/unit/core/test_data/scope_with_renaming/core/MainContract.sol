// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import {
    ParentContract
} from "./ParentContract.sol";

import {
    MainErrors as Errors
} from "./../errors/MainErrors.sol";


contract MainContract is ParentContract {

    
    function functionWithMainError1(uint256 a, uint256 b) external pure returns (uint256) {
        if (a == b) {
            revert Errors.MainError1();
        }
        // Add some arithmetic operations here
        return a + b;
    }

    function functionWithMainError2(uint256 a, uint256 b) external pure returns (uint256) {
        if (a < b) {
            revert Errors.MainError2();
        }
        // Add some arithmetic operations here
        return a - b;
    }

    function functionWithMainError3(uint256 a, uint256 b) external pure returns (uint256) {
        if (b == 0) {
            revert Errors.MainError3();
        }
        // Add some arithmetic operations here
        return a * b;
    }


}
