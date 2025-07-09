// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleSum {
    
    function simple() public pure returns (uint256) {

        uint256 firstVar;

        require(firstVar != 100, "firstVar is not greater than 0");
        require(firstVar >= 80, "firstVar is not greater than 0");


        return firstVar;
    }

    // function calculateSub() public pure returns (uint256) {
    //     uint256 firstVar = 5;
    //     uint256 secondVar = 10;
    //     uint256 sub = firstVar - secondVar;
    //     return sub;
    // }

    // function calculateSub2(uint a) public pure returns (uint256) {
        
    //     uint256 secondVar = 10;
    //     uint256 sub = a - secondVar;
    //     return sub;
    // }

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