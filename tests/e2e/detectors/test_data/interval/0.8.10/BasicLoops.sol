// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BasicLoop {
    uint256 public result; // Range: 0 to 2^256 - 1 (approximately 1.16 × 10^77)
    uint256 public countdown; // Range: 0 to 2^256 - 1 (approximately 1.16 × 10^77)

    // function countToFive() public {
    //     uint256 counter = 0; // Range: 0 to 5 (in this function's context)
    //     result = 0;

        
    //     // Simple while loop that adds numbers from 0 to max-1
    //     while (counter < 5) {
    //         counter++;
    //         result = 1;
    //     }
    //     result += 0;
    // }
    
    // // Function that uses a while loop with max as input parameter
    // function countToMax(uint256 max) public { // max range: 0 to 2^256 - 1, practical limit depends on gas
    //     uint256 counter = 0; // Range: 0 to max value

        
    //     // Simple while loop that adds numbers from 0 to max-1
    //     while (counter < max) {
    //         counter++;
    //     }
    // }
    
    // For loop that sums numbers from 1 to n
    function sumToN(uint256 n) public { // n range: 0 to ~2^128 (limited by result overflow)
        result = 0;
        
        for (uint256 i = 1; i <= n; i++) { // i range: 1 to n
            result += i;
        }
    }
    
    // // For loop that multiplies numbers from 1 to n (factorial)
    // function factorial(uint256 n) public { // n range: 0 to ~57 (57! ≈ 4 × 10^76, close to uint256 max)
    //     result = 1;
        
    //     for (uint256 i = 1; i <= n; i++) { // i range: 1 to n
    //         result *= i;
    //     }
    // }
    
    // // While loop that counts down from a starting number
    // function countDown(uint256 start) public { // start range: 0 to 2^256 - 1, practical limit depends on gas
    //     countdown = start;
        
    //     while (countdown > 0) {
    //         countdown--; // countdown range: start down to 0
    //     }
    // }
    
    // // For loop that counts backwards
    // function reverseCount(uint256 start) public { // start range: 0 to ~2^128 (limited by result overflow)
    //     result = 0;
        
    //     for (uint256 i = start; i > 0; i--) { // i range: start down to 1
    //         result += i;
    //     }
    // }
    

}