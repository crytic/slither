// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;


import {
    AccessControlErrors as Errors 
} from "../errors/ParentContractErrors.sol";


contract ParentContract {
     
     
    function functionWithAccessControlErrors1(uint256 a, uint256 b) external pure returns (uint256) {
        if (a == b) {
            revert Errors.AccessControlErrors1();
        }
        // Add some arithmetic operations here
        return a + b;
    }

    function functionWithAccessControlErrors2(uint256 a, uint256 b) external pure returns (uint256) {
        if (a < b) {
            revert Errors.AccessControlErrors2();
        }
        // Add some arithmetic operations here
        return a - b;
    }
  

}
