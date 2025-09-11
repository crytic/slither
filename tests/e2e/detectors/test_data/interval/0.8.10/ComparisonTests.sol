// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ComparisonTests {
    // Function 1: Greater than comparison
    function testGreaterThan() public pure returns (uint256) {
        uint a;
        require(a > 10);
        return a;
    }

    // Function 2: Less than comparison
    function testLessThan() public pure returns (uint256) {
        uint b;
        require(b < 100);
        return b;
    }

    // Function 3: Greater than or equal comparison
    function testGreaterEqual() public pure returns (uint256) {
        uint c;
        require(c >= 5);
        return c;
    }

    // Function 4: Less than or equal comparison
    function testLessEqual() public pure returns (uint256) {
        uint d;
        require(d <= 50);
        return d;
    }

    // Function 5: Equal comparison
    function testEqual() public pure returns (uint256) {
        uint e;
        require(e == 42);
        return e;
    }

    // Function 6: Not equal comparison
    function testNotEqual() public pure returns (uint256) {
        uint f;
        require(f != 10);
        return f;
    }

    // // Function 7: Multiple comparisons
    // function testMultipleComparisons() public pure returns (uint256) {
    //     uint g;
    //     require(g > 10);
    //     require(g < 100);
    //     require(g != 50);
    //     return g;
    // }

    // // Function 8: Variable comparison (placeholder for future implementation)
    // function testVariableComparison() public pure returns (uint256) {
    //     uint h;
    //     uint i;
    //     require(h > i);
    //     return h;
    // }
}
