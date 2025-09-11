// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ComparisonTests {
    // Function 1: Addition with two variables
    function addNumbers() public pure returns (uint256) {
        uint a;
        require(a > 10);
        return a;
    }
}
