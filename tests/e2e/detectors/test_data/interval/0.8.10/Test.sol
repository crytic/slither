// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test {
    
    function test(uint a) public pure returns (uint256) {
        require(a > 10);

        return a;
    }
   
}