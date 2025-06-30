// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

/**
 * @title ConstraintApplicationTest
 * @dev Comprehensive test contract to verify constraint application functionality
 * Tests that constraints are only applied when enforced by require() or assert()
 */
contract ConstraintApplicationTest {
    
    /**
     * @dev Test basic constraint application - direct comparison in require
     */
    function testDirectComparisonInRequire(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Direct comparison in require should apply constraint
        require(x > 50);  // Expected: x becomes [51, 255]
        
        return x;  // Expected: x is [51, 255]
    } // PASSED
    
    /**
     * @dev Test basic constraint application - direct comparison in assert
     */
    function testDirectComparisonInAssert(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Direct comparison in assert should apply constraint
        assert(x < 200);  // Expected: x becomes [0, 199]
        
        return x;  // Expected: x is [0, 199]
    } // PASSED
    
    /**
     * @dev Test that bare comparisons do NOT apply constraints
     */
    function testBareComparisonNoConstraint(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // These bare comparisons should NOT constrain x's interval
        bool comparison1 = x > 5;   // Expected: x remains [0, 255]
        bool comparison2 = x < 100; // Expected: x remains [0, 255]
        bool comparison3 = x == 50; // Expected: x remains [0, 255]
        
        // Only enforced constraints should apply
        require(comparison1);  // Expected: x becomes [6, 255]
        
        return x;  // Expected: x is [6, 255]
    } // PASSED
    
    /**
     * @dev Test constraint application for variable assigned comparison
     */
    function testVariableAssignedComparison(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Comparison assigned to variable should NOT apply constraint initially
        bool condition = x >= 25;  // Expected: x remains [0, 255]
        
        // Constraint should be applied when variable is used in require
        require(condition);  // Expected: x becomes [25, 255]
        
        return x;  // Expected: x is [25, 255]
    } // PASSED
    
    /**
     * @dev Test multiple constraints applied sequentially
     */
    function testMultipleConstraintsSequential(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Apply multiple constraints sequentially
        require(x > 10);   // Expected: x becomes [11, 255]
        require(x < 100);  // Expected: x becomes [11, 99]
        require(x != 50);  // Expected: x becomes [11, 49] or [51, 99]
        
        return x;  // Expected: x is [11, 49] or [51, 99]
    } // FAILED: current implementation does not handle != operator
    
    /**
     * @dev Test multiple variables with different constraints
     */
    function testMultipleVariables(uint8 x, uint8 y) public pure returns (uint8) {
        // x and y start with bounds [0, 255]
        
        // Store comparisons as variables
        bool xCondition = x > 50;     // Expected: x remains [0, 255]
        bool yCondition = y < 200;    // Expected: y remains [0, 255]
        
        // Apply constraints
        require(xCondition);  // Expected: x becomes [51, 255]
        require(yCondition);  // Expected: y becomes [0, 199]
        
        return x + y;  // Expected: x is [51, 255], y is [0, 199]
    } // PASSED
    
    /**
     * @dev Test complex constraint with multiple variables
     */
    function testComplexConstraint(uint8 x, uint8 y) public pure returns (uint8) {
        // x and y start with bounds [0, 255]
        
        // Complex condition involving multiple variables
        bool complexCondition = x > y && y > 10;  // Expected: x and y remain [0, 255]
        
        // Apply the complex constraint
        require(complexCondition);  // Expected: x > y and y > 10
        
        return x - y;  // Expected: x > y, so result is positive
    } // FAILED: current implementation does not handle && operator?
    
    /**
     * @dev Test that unused constraints are not applied
     */
    function testUnusedConstraints(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Create multiple constraints but only use some
        bool condition1 = x > 10;   // Expected: x remains [0, 255]
        bool condition2 = x < 100;  // Expected: x remains [0, 255]
        bool condition3 = x == 50;  // Expected: x remains [0, 255]
        
        // Only apply condition1 and condition2
        require(condition1);  // Expected: x becomes [11, 255]
        require(condition2);  // Expected: x becomes [11, 99]
        // condition3 is never used, so it should not affect x's bounds
        
        return x;  // Expected: x is [11, 99]
    } // PASSED
    
    /**
     * @dev Test constraint application in conditional blocks
     */
    function testConstraintInConditional(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        if (x > 50) {
            // Inside this block, x > 50 should be enforced
            require(x < 100);  // Expected: x becomes [51, 99]
        } else {
            // Inside this block, x <= 50 should be enforced
            require(x > 10);   // Expected: x becomes [11, 50]
        }
        
        return x;  // Expected: x is [11, 50] or [51, 99]
    } // FAILED: it keeps the original bounds for x, but it has right bounds for x inside the if/else block. But, it ignores the constraint for x > 50 in the else block.
    
    /**
     * @dev Test that constraints are properly applied for different comparison types
     */
    function testDifferentComparisonTypes(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Test different comparison operators
        bool greaterThan = x > 25;      // Expected: x remains [0, 255]
        bool greaterEqual = x >= 50;    // Expected: x remains [0, 255]
        bool lessThan = x < 200;        // Expected: x remains [0, 255]
        bool lessEqual = x <= 150;      // Expected: x remains [0, 255]
        bool equal = x == 100;          // Expected: x remains [0, 255]
        bool notEqual = x != 0;         // Expected: x remains [0, 255]
        
        // Apply constraints
        require(greaterThan);   // Expected: x becomes [26, 255]
        require(lessThan);      // Expected: x becomes [26, 199]
        
        return x;  // Expected: x is [26, 199]
    } // PASSED
    
    /**
     * @dev Test constraint application with constants on both sides
     */
    function testConstantComparisons(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Test comparisons with constants
        bool condition1 = 10 < x;       // Expected: x remains [0, 255]
        bool condition2 = x < 100;      // Expected: x remains [0, 255]
        bool condition3 = 50 == x;      // Expected: x remains [0, 255]
        
        // Apply constraints
        require(condition1);  // Expected: x becomes [11, 255]
        require(condition2);  // Expected: x becomes [11, 99]
        
        return x;  // Expected: x is [11, 99]
    }
    
    /**
     * @dev Test that constraints work correctly with arithmetic operations
     */
    function testConstraintWithArithmetic(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Test constraint with arithmetic
        bool condition = x + 10 > 50;  // Expected: x remains [0, 255]
        
        // Apply constraint
        require(condition);  // Expected: x + 10 > 50, so x > 40
        
        return x;  // Expected: x is [41, 255]
    } // FAILED
    
    /**
     * @dev Test that constraints are properly scoped to the function
     */
    function testConstraintScoping(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        
        // Apply constraint in this function
        require(x > 25);  // Expected: x becomes [26, 255]
        
        return x;  // Expected: x is [26, 255]
    } // PASSED
    
    /**
     * @dev Test that constraints from one function don't affect another
     */
    function testConstraintIsolation(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255] (not affected by other functions)
        
        // Apply different constraint
        require(x < 100);  // Expected: x becomes [0, 99]
        
        return x;  // Expected: x is [0, 99]
    } // PASSED
} 