// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test {
    
    function test(uint a) public pure returns (uint256) {
        assert(a >= 10);
        assert(a <= 30);

    
        return a-11;
    }
   
}