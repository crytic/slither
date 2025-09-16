// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleIf {
    // // Test: Greater than
    // function testGreaterThan(uint256 x) public pure {
    //     if (x > 100) {
    //         x = 5;
    //     }
    //     x += 0; // x should be [0, 100] and 5 should be in the valid values
    // } // PASSED
    // // Test: Less than
    // function testLessThan(uint256 x) public pure {
    //     if (x < 50) {
    //         x = 10;
    //     }
    //     x += 1; // x should be [11, 11] U [51, infinity] and 11 should be in the valid values
    // } // PASSED
    // // Test: Greater than or equal
    // function testGreaterOrEqual(uint256 x) public pure {
    //     if (x >= 100) {
    //         x = 5;
    //     }
    //     x += 1; // x should be [1, 100] and 6 should be in the valid values
    // } // PASSED
    // // Test: Less than or equal
    // function testLessOrEqual(uint256 x) public pure {
    //     if (x <= 50) {
    //         x = 10;
    //     }
    //     x += 1; // x should be [11, 11] U [52, infinity] and 11 should be in the valid values
    // } // PASSED
    // // Test: Equal
    // function testEqual(uint256 x) public pure {
    //     if (x == 100) {
    //         x = 5;
    //     }
    //     x += 0; // x should be [0, 99] U [101, infinity] U {5} and 5 should be in the valid values
    // }
    // // Test: Not equal
    // function testNotEqual(uint256 x) public pure {
    //     if (x != 100) {
    //         x = 5;
    //     }
    //     x += 1;
    // } // x should be {101, 6}
    // function two_ifs(uint256 x) public pure {
    //     if (x > 100) {
    //         x = 5;
    //     } // at this stage, x should be [0,100] and valid values are {5}
    //     if (x <= 100) {
    //         // which means it goes in here.
    //         x = 10; //here it gets set to 10
    //     }
    //     x += 0;
    // } //x should be {10}
    // function if_else(uint256 x) public pure {
    //     if (x > 100) {
    //         x = 5;
    //     } else {
    //         x += 1;
    //     }
    //     x += 0;
    // } // x should be {5} [1,101]
    // function test(uint x) public pure returns (uint) {
    //     if (x > 100) {
    //         x = 5;
    //     } else if (x > 50) {
    //         x = 25;
    //     } else {
    //         x += 10;
    //     }
    //     x += 0;
    //     return x;
    // } // x should be {5, 25} [10, 60]
    // function nested_if(uint256 x) public pure {
    //     if (x > 100) {
    //         x = 5;
    //         if (x == 101) {
    //             x = 11;
    //         }
    //     }
    //     x += 0;
    // } // x should be {5} U [0,100]
    // function if_test(uint256 x) public pure {
    //     x = 5;
    //     if (x < 100) {
    //         x = 6;
    //     }
    //     x += 0;
    // } // x should be {6}
    // function nested_if2(uint256 x) public pure {
    //     if (x > 100) {
    //         if (x == 105) {
    //             x = 11;
    //         }
    //     }
    //     x += 0;
    // } // x should be {11} U [0, 100] U [101, 104] U [106,max]
    // function nested_if3(uint256 x) public pure {
    //     if (x > 50) {
    //         if (x > 100) {
    //             if (x == 150) {
    //                 x = 25;
    //             }
    //         }
    //     }
    //     x += 0;
    // } // x should be {25} U  [0, 50] U [51, 100] U [101, 149] U [151, max]
    // function testLessThan2(uint256 x) public pure {
    //     require(x <= 50); // [0,50]
    //     x += 10; // [10, 60]
    //     if (x < 50) {
    //         x = 10;
    //     }
    //     x += 1;
    // }
}
