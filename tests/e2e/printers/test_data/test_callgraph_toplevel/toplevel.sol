// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Top level function that adds two numbers
function add(uint256 a, uint256 b) pure returns (uint256) {
    return a + b;
}

// Top level function that multiplies two numbers
function multiply(uint256 a, uint256 b) pure returns (uint256) {
    return a * b;
}

// Top level function that calls other top level functions
function calculate(uint256 x, uint256 y) pure returns (uint256) {
    uint256 sum = add(x, y);
    uint256 product = multiply(x, y);
    return add(sum, product);
}

contract Calculator {
    uint256 public result;

    function compute(uint256 a, uint256 b) external {
        // Contract calling top level function
        result = calculate(a, b);
    }

    function simpleAdd(uint256 a, uint256 b) external pure returns (uint256) {
        // Contract calling top level function
        return add(a, b);
    }
}
