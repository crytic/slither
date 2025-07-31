// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BasicWhileLoop {
    uint256 public result;
    
    // Function that uses a while loop with max as input parameter
    function countToMax(uint256 max) public {
        uint256 counter = 0;
        result = 0;
        result = 1;
        result = 2;
        result = 3;
        result = 0;
        
        // Simple while loop that adds numbers from 0 to max-1
        while (counter < max) {
            result += counter;
            counter++;
        }
    }
    
    // Function to get the current result
    function getResult() public view returns (uint256) {
        return result;
    }
}