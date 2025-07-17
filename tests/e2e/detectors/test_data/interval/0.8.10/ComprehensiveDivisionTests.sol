// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

/**
 * @title ComprehensiveDivisionTests
 * @dev Test all division constraint cases (positive/negative constants × 4 operators)
 */
contract ComprehensiveDivisionTests {
    
    // ========================================
    // POSITIVE CONSTANT DIVISION TESTS (x / constant)
    // ========================================
    
    /**
     * @dev Test: x / 2 < 25
     * Expected: x / 2 < 25 => x < 50 => x <= 49 => x ∈ [0, 49]
     */
    function testPositiveDivisionLess(uint8 x) public pure returns (uint8) {
        require(x / 2 < 25);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x / 2 <= 25
     * Expected: x / 2 <= 25 => x <= 50 => x ∈ [0, 50]
     */
    function testPositiveDivisionLessEqual(uint8 x) public pure returns (uint8) {
        require(x / 2 <= 25);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x / 2 > 25
     * Expected: x / 2 > 25 => x > 50 => x >= 51 => x ∈ [51, 255]
     */
    function testPositiveDivisionGreater(uint8 x) public pure returns (uint8) {
        require(x / 2 > 25);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x / 2 >= 25
     * Expected: x / 2 >= 25 => x >= 50 => x ∈ [50, 255]
     */
    function testPositiveDivisionGreaterEqual(uint8 x) public pure returns (uint8) {
        require(x / 2 >= 25);
        return x;
    } // PASSED
    
    // // ========================================
    // // NEGATIVE CONSTANT DIVISION TESTS (x / negative)
    // // ========================================
    
    /**
     * @dev Test: x / (-2) < 25
     * Expected: x / (-2) < 25 => x > -50 => x >= -49 => x ∈ [-49, 127]
     */
    function testNegativeDivisionLess(int8 x) public pure returns (int8) {
        require(x / -2 < 25);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x / (-2) <= 25
     * Expected: x / (-2) <= 25 => x >= -50 => x ∈ [-50, 127]
     */
    function testNegativeDivisionLessEqual(int8 x) public pure returns (int8) {
        require(x / (-2) <= 25);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x / (-2) > 25
     * Expected: x / (-2) > 25 => x < -50 => x <= -51 => x ∈ [-128, -51]
     */
    function testNegativeDivisionGreater(int8 x) public pure returns (int8) {
        require(x / (-2) > 25);
        return x;
    } // PASSED
    
    /**
     * @dev Test: x / (-2) >= 25
     * Expected: x / (-2) >= 25 => x <= -50 => x ∈ [-128, -50]
     */
    function testNegativeDivisionGreaterEqual(int8 x) public pure returns (int8) {
        require(x / (-2) >= 25);
        return x;
    } // PASSED
    
    // // ========================================
    // // CONSTANT / VARIABLE TESTS (constant / x)
    // // ========================================
    
    /**
     * @dev Test: 100 / x < 4
     * Expected: 100 / x < 4 => x > 25 => x >= 26 => x ∈ [26, 255]
     */
    function testConstantDividedByVariableLess(uint8 x) public pure returns (uint8) {
        require(x > 0); // Prevent division by zero
        require(100 / x < 4);
        return x;
    } // PASSED
    
    /**
     * @dev Test: 100 / x <= 4
     * Expected: 100 / x <= 4 => x >= 25 => x ∈ [25, 255]
     */
    function testConstantDividedByVariableLessEqual(uint8 x) public pure returns (uint8) {
        require(x > 0); // Prevent division by zero
        require(100 / x <= 4);
        return x;
    } // PASSED
    
    /**
     * @dev Test: 100 / x > 4
     * Expected: 100 / x > 4 => x < 25 => x <= 24 => x ∈ [1, 24]
     */
    function testConstantDividedByVariableGreater(uint8 x) public pure returns (uint8) {
        require(x > 0); // Prevent division by zero
        require(100 / x > 4);
        return x;
    } // PASSED
    
    /**
     * @dev Test: 100 / x >= 4
     * Expected: 100 / x >= 4 => x <= 25 => x ∈ [1, 25]
     */
    function testConstantDividedByVariableGreaterEqual(uint8 x) public pure returns (uint8) {
        require(x > 0); // Prevent division by zero
        require(100 / x >= 4);
        return x;
    } // PASSED
    
    // // ========================================
    // // NEGATIVE CONSTANT / VARIABLE TESTS
    // // ========================================
    
    /**
     * @dev Test: (-100) / x < -4
     * Expected: (-100) / x < -4 -> -100 < -4x -> 25 > x -> [1, 24]
     */
    function testNegativeConstantDividedByVariableLess(int8 x) public pure returns (int8) {
        require(x > 0); // Prevent division by zero
        require((-100) / x < -4);
        return x;
    } // PASSED
    
    /**
     * @dev Test: (-100) / x >= -4
     * Expected: (-100) / x >= -4 -> x >= 25 => x ∈ [25, 127]
     */
    function testNegativeConstantDividedByVariableGreaterEqual(int8 x) public pure returns (int8) {
        require(x > 0); // Prevent division by zero
        require((-100) / x >= -4);
        return x;
    }
    
    // // ========================================
    // // EDGE CASE TESTS
    // // ========================================
    
    /**
     * @dev Test: x / 3 > 16
     * Expected: x / 3 > 16 => x > 48 => x >= 49 => x ∈ [49, 255]
     */
    function testDivisionByThree(uint8 x) public pure returns (uint8) {
        require(x / 3 > 16);
        return x;
    }
    
    /**
     * @dev Test: x / (-1) < 50
     * Expected: x / (-1) < 50 => x > -50 => x >= -49 => x ∈ [-49, 127]
     */
    function testDivisionByNegativeOne(int8 x) public pure returns (int8) {
        require(x / (-1) < 50);
        return x;
    }
}