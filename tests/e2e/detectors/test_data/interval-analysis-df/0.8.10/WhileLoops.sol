// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BasicWhileLoop {
    uint256 public result;

    function countToFive() public {
        uint256 counter = 0;
        result = 0;

        // Simple while loop that adds numbers from 0 to max-1
        while (counter < 5) {
            counter++;
            result = 1;
        }
    }
}
