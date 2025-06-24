// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleSum {
    
    function calculateSum() public pure returns (uint256) {
        uint256 firstVar = 5;
        uint256 secondVar = 10;
        uint256 sum = firstVar + secondVar;
        return sum;
    }

    function calculateSub() public pure returns (uint256) {
        uint256 firstVar = 5;
        uint256 secondVar = 10;
        uint256 sub = firstVar - secondVar;
        return sub;
    }

    function calculateSub2(uint a) public pure returns (uint256) {
        
        uint256 secondVar = 10;
        uint256 sub = a - secondVar;
        return sub;
    }

    // function calculateMul() public pure returns (uint256) {
    //     uint256 firstVar = 5;
    //     uint256 secondVar = 10;
    //     uint256 mul = firstVar * secondVar;
    //     return mul;
    // }

    // function calculateMul(uint a) public pure returns (uint256) {
    //     uint256 secondVar = 10;
    //     uint256 mul = a * secondVar;
    //     return mul;
    // }

    // function calculateDiv() public pure returns (uint256) {
    //     uint256 firstVar = 5;
    //     uint256 secondVar = 10;
    //     uint256 div = secondVar/ firstVar;
    //     return div;
    // }

   
   
}