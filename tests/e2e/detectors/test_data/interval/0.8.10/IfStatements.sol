// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleIf {
    
    // Test: Greater than
    function testGreaterThan(uint256 x) public pure {
        if (x > 100) {
            x = 5;
        }
        x += 0; // x should be [0, 100] and 5 should be in the valid values
    } // PASSED
    
    // Test: Less than
    function testLessThan(uint256 x) public pure {
        if (x < 50) {
            x = 10;
        }
        x += 1; // x should be [11, 11] U [51, infinity] and 11 should be in the valid values
    } // PASSED
    
    // Test: Greater than or equal
    function testGreaterOrEqual(uint256 x) public pure {
        if (x >= 100) {
            x = 5;
        }
        x += 1; // x should be [1, 100] and 6 should be in the valid values
    } // PASSED
    
    // Test: Less than or equal
    function testLessOrEqual(uint256 x) public pure {
        if (x <= 50) {
            x = 10;
        }
        x += 1; // x should be [11, 11] U [52, infinity] and 11 should be in the valid values
    } // PASSED
    
    // Test: Equal
    function testEqual(uint256 x) public pure {
        if (x == 100) {
            x = 5;
        }
        x += 0; // x should be [0, 99] U [101, infinity] U {5} and 5 should be in the valid values
    }
    
    // Test: Not equal
    function testNotEqual(uint256 x) public pure {
        if (x != 100) {
            x = 5;
        }
        x += 1; 
    } // x should be {101, 6}

    // function testIfElse(uint256 x) public pure {
    //     if (x > 100) {
    //         x = 5;
    //     } else {
    //         x = 10;
    //     }
    //     x += 0;
    // } //x should be {5, 10}
}