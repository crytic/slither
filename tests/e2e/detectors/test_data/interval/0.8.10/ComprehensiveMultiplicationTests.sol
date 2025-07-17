// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

/**
 * @title ComprehensiveMultiplicationTests
 * @dev Test all multiplication constraint cases (positive/negative constants × 4 operators)
 */
contract ComprehensiveMultiplicationTests {
    
    // ========================================
    // POSITIVE CONSTANT MULTIPLICATION TESTS
    // ========================================
    
    /**
     * @dev Test: x * 2 < 100
     * Expected: x * 2 < 100 => x < 50 => x <= 49 => x ∈ [0, 49]
     */
    function testPositiveMultiplicationLess(uint8 x) public pure returns (uint8) {
        require(x * 2 < 100);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * 2 <= 100
     * Expected: x * 2 <= 100 => x <= 50 => x ∈ [0, 50]
     */
    function testPositiveMultiplicationLessEqual(uint8 x) public pure returns (uint8) {
        require(x * 2 <= 100);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * 2 > 100
     * Expected: x * 2 > 100 => x > 50 => x >= 51 => x ∈ [51, 255]
     */
    function testPositiveMultiplicationGreater(uint8 x) public pure returns (uint8) {
        require(x * 2 > 100);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * 2 >= 100
     * Expected: x * 2 >= 100 => x >= 50 => x ∈ [50, 255]
     */
    function testPositiveMultiplicationGreaterEqual(uint8 x) public pure returns (uint8) {
        require(x * 2 >= 100);
        return x;
    } // PASSED
    
    // // // ========================================
    // // // NEGATIVE CONSTANT MULTIPLICATION TESTS
    // // // ========================================
    
    /**
     * @dev Test: x * (-2) < -100
     * Expected: x * (-2) < -100 => x > 50 => x >= 51 => x ∈ [51, 127]
     */
    function testNegativeMultiplicationLess(int8 x) public pure returns (int8) {
        require(x * (-2) < -100);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * (-2) <= -100
     * Expected: x * (-2) <= -100 => x >= 50 => x ∈ [50, 127]
     */
    function testNegativeMultiplicationLessEqual(int8 x) public pure returns (int8) {
        require(x * (-2) <= -100);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * (-2) > -100
     * Expected: x * (-2) > -100 => x < 50 => x <= 49 => x ∈ [-128, 49]
     */
    function testNegativeMultiplicationGreater(int8 x) public pure returns (int8) {
        require(x * (-2) > -100);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * (-2) >= -100
     * Expected: x * (-2) >= -100 => x <= 50 => x ∈ [-128, 50]
     */
    function testNegativeMultiplicationGreaterEqual(int8 x) public pure returns (int8) {
        require(x * (-2) >= -100);
        return x;
    } // PASSED
    
    // // // ========================================
    // // // EDGE CASE TESTS
    // // // ========================================
    
    /**
     * @dev Test: x * (-1) > -50
     * Expected: x * (-1) > -50 => x < 50 => x <= 49 => x ∈ [-128, 49]
     */
    function testNegativeOneMultiplication(int8 x) public pure returns (int8) {
        require(x * (-1) > -50);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * 3 < 150
     * Expected: x * 3 < 150 => x < 50 => x <= 49 => x ∈ [0, 49]
     */
    function testLargerPositiveMultiplication(uint8 x) public pure returns (uint8) {
        require(x * 3 < 150);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x * (-5) >= -250
     * Expected: x * (-5) >= -250 => x <= 50 => x ∈ [-128, 50]
     */
    function testLargerNegativeMultiplication(int8 x) public pure returns (int8) {
        require(x * (-5) >= -250);
        return x;
    } // PASSED
    
}