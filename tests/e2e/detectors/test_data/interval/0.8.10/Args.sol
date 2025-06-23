// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Args {
    
   
    function foo(uint a) public pure returns (uint256) {
        uint b = 20;
        uint c = a + b;
        return c;
    }

    function bar() public pure returns (uint256) {
        uint a = 10;
        uint b = 20;
        uint c = a + b;
        return c;
    }
}