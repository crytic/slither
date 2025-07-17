// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

/**
 * @title ConstraintApplicationTest
 * @dev Comprehensive test contract to verify constraint application functionality
 * Tests that constraints are only applied when enforced by require() or assert()
 */
contract ConstraintApplicationTest {
    
    // ========================================
    // BASIC CONSTRAINT APPLICATION TESTS
    // ========================================
    
    /**
     * @dev Test basic constraint application - direct comparison in require
     */
    function testDirectComparisonInRequire(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        require(x > 50);  // Expected: x becomes [51, 255]
        return x;  // Expected: x is [51, 255]
    } // PASSED
    
    /**
     * @dev Test basic constraint application - direct comparison in assert
     */
    function testDirectComparisonInAssert(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        assert(x < 200);  // Expected: x becomes [0, 199]
        return x;  // Expected: x is [0, 199]
    } // PASSED
    
    /**
     * @dev Test that bare comparisons do NOT apply constraints
     */
    function testBareComparisonNoConstraint(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool comparison1 = x > 5;   // Expected: x remains [0, 255]
        bool comparison2 = x < 100; // Expected: x remains [0, 255]
        bool comparison3 = x == 50; // Expected: x remains [0, 255]
        require(comparison1);  // Expected: x becomes [6, 255]
        
        return x;  // Expected: x is [6, 255]
    } // PASSED
    
    // // // ========================================
    // // // VARIABLE ASSIGNMENT TESTS
    // // // ========================================
    
    /**
     * @dev Test constraint application for variable assigned comparison
     */
    function testVariableAssignedComparison(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition = x >= 25;  // Expected: x remains [0, 255]
        require(condition);  // Expected: x becomes [25, 255]
        return x;  // Expected: x is [25, 255]
    } // PASSED
    
    /**
     * @dev Test multiple variables with different constraints
     */
    function testMultipleVariables(uint8 x, uint8 y) public pure returns (uint8) {
        // x and y start with bounds [0, 255]
        bool xCondition = x > 50;     // Expected: x remains [0, 255]
        bool yCondition = y < 200;    // Expected: y remains [0, 255]
        require(xCondition);  // Expected: x becomes [51, 255]
        require(yCondition);  // Expected: y becomes [0, 199]
        return x + y;  // Expected: x is [51, 255], y is [0, 199]
    } // PASSED
    
    // // // ========================================
    // // // COMPARISON OPERATOR TESTS
    // // // ========================================
    
    /**
     * @dev Test all comparison operators
     */
    function testAllComparisonOperators(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool greaterThan = x > 25;      // Expected: x remains [0, 255]
        bool greaterEqual = x >= 50;    // Expected: x remains [0, 255]
        bool lessThan = x < 200;        // Expected: x remains [0, 255]
        bool lessEqual = x <= 150;      // Expected: x remains [0, 255]
        bool equal = x == 100;          // Expected: x remains [0, 255]
        bool notEqual = x != 0;         // Expected: x remains [0, 255]
        
        require(greaterThan);   // Expected: x becomes [26, 255]
        require(lessThan);      // Expected: x becomes [26, 199]
        
        return x;  // Expected: x is [26, 199]
    } // PASSED
    
    /**
     * @dev Test constant comparisons (constant on left side)
     */
    function testConstantComparisons(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition1 = 10 < x;       // Expected: x remains [0, 255]
        bool condition2 = x < 100;      // Expected: x remains [0, 255]
        bool condition3 = 50 == x;      // Expected: x remains [0, 255]
        
        require(condition1);  // Expected: x becomes [11, 255]
        require(condition2);  // Expected: x becomes [11, 99]
        
        return x;  // Expected: x is [11, 99]
    } // PASSED
    
    // // ========================================
    // // ARITHMETIC CONSTRAINT TESTS
    // // ========================================
    
    /**
     * @dev Test constraint with arithmetic operations
     */
    function testArithmeticConstraint(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition = x + 10 > 50;  // Expected: x remains [0, 255]
        require(condition);  // Expected: x + 10 > 50, so x > 40
        return x;  // Expected: x is [41, 255]
    } // PASSED

    
    /**
     * @dev Test constraint with subtraction
     */
    function testSubtractionConstraint(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition = x - 5 > 10;  // Expected: x remains [0, 255]
        require(condition);  // Expected: x - 5 > 10, so x > 15
        return x;  // Expected: x is [16, 255]
    } // PASSED
    
    /**
     * @dev Test constraint with multiplication
     */
    function testMultiplicationConstraint(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition = x * 2 > 100;  // Expected: x remains [0, 255]
        require(condition);  // Expected: x * 2 > 100, so x > 50
        return x;  // Expected: x is [51, 255]
    }
    
    // // // ========================================
    // // // MULTIPLE CONSTRAINT TESTS
    // // // ========================================
    
    /**
     * @dev Test multiple constraints applied sequentially
     */
    function testMultipleConstraintsSequential(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        require(x > 10);   // Expected: x becomes [11, 255]
        require(x < 100);  // Expected: x becomes [11, 99]
        require(x != 50);  // Expected: x becomes [11, 49] or [51, 99]
        return x;  // Expected: x is [11, 49] or [51, 99]
    } // PASSED
    
    /**
     * @dev Test that unused constraints are not applied
     */
    function testUnusedConstraints(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition1 = x > 10;   // Expected: x remains [0, 255]
        bool condition2 = x < 100;  // Expected: x remains [0, 255]
        bool condition3 = x == 50;  // Expected: x remains [0, 255]
        
        require(condition1);  // Expected: x becomes [11, 255]
        require(condition2);  // Expected: x becomes [11, 99]
        // condition3 is never used, so it should not affect x's bounds
        
        return x;  // Expected: x is [11, 99]
    } // PASSED
    
    // // // ========================================
    // // // SCOPE AND ISOLATION TESTS
    // // // ========================================
    
    /**
     * @dev Test that constraints are properly scoped to the function
     */
    function testConstraintScoping(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        require(x > 25);  // Expected: x becomes [26, 255]
        return x;  // Expected: x is [26, 255]
    } // PASSED
    
    /**
     * @dev Test that constraints from one function don't affect another
     */
    function testConstraintIsolation(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255] (not affected by other functions)
        require(x < 100);  // Expected: x becomes [0, 99]
        return x;  // Expected: x is [0, 99]
    }
    
    // // // ========================================
    // // // EDGE CASE TESTS
    // // // ========================================
    
    /**
     * @dev Test boundary conditions
     */
    function testBoundaryConditions(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        require(x >= 0);   // Expected: x remains [0, 255] (no change)
        require(x <= 255); // Expected: x remains [0, 255] (no change)
        return x;  // Expected: x is [0, 255]
    } // PASSED
    
    /**
     * @dev Test equality constraints
     */
    function testEqualityConstraints(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        require(x == 100);  // Expected: x becomes [100, 100]
        return x;  // Expected: x is [100, 100]
    } // PASSED
    
    /**
     * @dev Test inequality constraints
     */
    function testInequalityConstraints(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        require(x != 50);  // Expected: x becomes [0, 49] or [51, 255]
        return x;  // Expected: x is [0, 49] or [51, 255]
    } // PASSED
    

    
    // // // ========================================
    // // // ADDITIONAL LOGICAL OPERATOR TESTS
    // // // ========================================
    
    /**
     * @dev Test multiple AND conditions
     */
    function testMultipleAndConditions(uint8 x, uint8 y, uint8 z) public pure returns (uint8) {
        // x, y, z start with bounds [0, 255]
        bool condition = x > 10 && y > 20 && z > 30;  // Expected: all remain [0, 255]
        require(condition);  // Expected: x > 10 AND y > 20 AND z > 30
        return x + y + z;  // Expected: x > 10, y > 20, z > 30
    } // PASSED
    
} 