// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ConstraintTest {
    
    // Test Case 1: Simple guard prevents overflow
    // function testSimpleGuard(uint256 x) public pure returns (uint256) {
    //     require(x <= 150, "Input too large");
    //     return x + 100;
    // }

    // Test Case 1: Simple guard prevents overflow
    function testSimpleGuard2(uint256 x) public pure returns (uint256) {
        require(x <= 50 && x >= 30, "Input too large");

        require(x <= 200, "Input too large");
        // require(x <= 200, "Input too large");
        return x + 30;
    }

    // function testSimpleGuard3(uint256 x) public pure returns (uint256) {
    //     uint y = 23;
    //     require(x <= 150 && x >= 23, "Input too large");
    //     return x + 100;
    // }
    
    // function testSimpleGuard2(uint8 x) public pure returns (uint8) {
    //     // require(x > 150, "Input too large");
    //     uint y = 3 + 6+ 56+7;
    //     return x + 100;
    // }
    
}