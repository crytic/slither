// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

/**
 * @title ComparisonApplicationTest
 * @dev Comprehensive test contract to verify constraint application functionality
 * Tests that constraints are only applied when enforced by require() or assert()
 */
contract ComprarisonApplicationTest {
    // ========================================
    // BASIC CONSTRAINT APPLICATION TESTS
    // ========================================
    /**
     * @dev Test basic constraint application - direct comparison in require
     */
    function testDirectComparisonInRequire(
        uint8 x
    ) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        require(x > 50); // Expected: x becomes [51, 255]
        return x; // Expected: x is [51, 255]
    } // PASSED

    /**
     * @dev Test basic constraint application - direct comparison in assert
     */
    function testDirectComparisonInAssert(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        assert(x < 200); // Expected: x becomes [0, 199]
        return x; // Expected: x is [0, 199]
    } // PASSED

    /**
     * @dev Test that bare comparisons do NOT apply constraints
     */
    function testBareComparisonNoConstraint(
        uint8 x
    ) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool comparison1 = x > 5; // Expected: x remains [0, 255]
        bool comparison2 = x < 100; // Expected: x remains [0, 255]
        bool comparison3 = x == 50; // Expected: x remains [0, 255]
        require(comparison1); // Expected: x becomes [6, 255]
        return x; // Expected: x is [6, 255]
    }

    // // // // ========================================
    // // // // VARIABLE ASSIGNMENT TESTS
    // // // // ========================================
    /**
     * @dev Test constraint application for variable assigned comparison
     */
    function testVariableAssignedComparison(
        uint8 x
    ) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition = x >= 25; // Expected: x remains [0, 255]
        require(condition); // Expected: x becomes [25, 255]
        return x; // Expected: x is [25, 255]
    } // PASSED

    /**
    //  * @dev Test multiple variables with different constraints
    //  */
    function testMultipleVariables(
        uint8 x,
        uint8 y
    ) public pure returns (uint8) {
        // x and y start with bounds [0, 255]
        bool xCondition = x > 50; // Expected: x remains [0, 255]
        bool yCondition = y < 200; // Expected: y remains [0, 255]
        require(xCondition); // Expected: x becomes [51, 255]
        require(yCondition); // Expected: y becomes [0, 199]
        return x + y; // Expected: x is [51, 255], y is [0, 199]
    } // PASSED

    // // // // // ========================================
    // // // // // COMPARISON OPERATOR TESTS
    // // // // // ========================================
    /**
     * @dev Test all comparison operators
     */
    function testAllComparisonOperators(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool greaterThan = x > 25; // Expected: x remains [0, 255]
        bool greaterEqual = x >= 50; // Expected: x remains [0, 255]
        bool lessThan = x < 200; // Expected: x remains [0, 255]
        bool lessEqual = x <= 150; // Expected: x remains [0, 255]
        bool equal = x == 100; // Expected: x remains [0, 255]
        bool notEqual = x != 0; // Expected: x remains [0, 255]
        require(greaterThan); // Expected: x becomes [26, 255]
        require(lessThan); // Expected: x becomes [26, 199]
        return x; // Expected: x is [26, 199]
    } // PASSED

    /**
     * @dev Test constant comparisons (constant on left side)
     */
    function testConstantComparisons(uint8 x) public pure returns (uint8) {
        // x starts with bounds [0, 255]
        bool condition1 = 10 < x; // Expected: x remains [0, 255]
        bool condition2 = x < 100; // Expected: x remains [0, 255]
        bool condition3 = 50 == x; // Expected: x remains [0, 255]
        require(condition1); // Expected: x becomes [11, 255]
        require(condition2); // Expected: x becomes [11, 99]
        return x; // Expected: x is [11, 99]
    } // PASSED
}
