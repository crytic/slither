// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ArithmeticTests {
    // Function 1: Addition with two variables
    function addNumbers() public pure returns (uint256) {
        uint256 a = 15;
        uint256 b = 25;
        uint256 result = a + b;
        return result;
    }

    // Function 2: Subtraction with two variables
    function subtractNumbers() public pure returns (uint256) {
        uint256 x = 100;
        uint256 y = 30;
        uint256 result = x - y;
        return result;
    }

    // Function 3: Multiplication with one variable (squared)
    function squareNumber() public pure returns (uint256) {
        uint256 num = 8;
        uint256 result = num * num;
        return result;
    }

    // Function 4: Division with two variables
    function divideNumbers() public pure returns (uint256) {
        uint256 dividend = 144;
        uint256 divisor = 12;
        uint256 result = dividend / divisor;
        return result;
    }

    // Function 5: Multiplication with two variables
    function multiplyNumbers() public pure returns (uint256) {
        uint256 a = 9;
        uint256 b = 7;
        uint256 result = a * b;
        return result;
    }

    // Function 6: Power operation (manual)
    function cubedNumber() public pure returns (uint256) {
        uint256 base = 4;
        uint256 result = base * base * base;
        return result;
    }

    // Function 7: Average of two numbers
    function averageNumbers() public pure returns (uint256) {
        uint256 first = 20;
        uint256 second = 30;
        uint256 result = (first + second) / 2;
        return result;
    }

    // Function 8: Complex expression with two variables
    function complexCalculation() public pure returns (uint256) {
        uint256 x = 6;
        uint256 y = 4;
        uint256 result = (x + y) * (x - y);
        return result;
    }

    // Function 9: Increment and multiply
    function incrementAndMultiply() public pure returns (uint256) {
        uint256 value = 7;
        uint256 result = (value + 1) * 3;
        return result;
    }

    // Function 10: Percentage calculation
    function calculatePercentage() public pure returns (uint256) {
        uint256 total = 200;
        uint256 percentage = 15;
        uint256 result = (total * percentage) / 100;
        return result;
    }

    // Function 11: Area of rectangle
    function rectangleArea() public pure returns (uint256) {
        uint256 length = 12;
        uint256 width = 8;
        uint256 result = length * width;
        return result;
    }

    // Function 12: Simple compound interest calculation
    function simpleInterest() public pure returns (uint256) {
        uint256 principal = 1000;
        uint256 rate = 5; // 5%
        uint256 result = principal + ((principal * rate) / 100);
        return result;
    }
}
