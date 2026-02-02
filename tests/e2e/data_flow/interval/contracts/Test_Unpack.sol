// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Unpack Operation
/// @dev Tests tuple unpacking from function returns
contract Test_Unpack {
    // =========================================================================
    // Helper Functions - Return tuples with known values
    // =========================================================================

    function returnTwo() internal pure returns (uint256, uint256) {
        return (10, 20);
    }

    function returnThree() internal pure returns (uint256, uint256, uint256) {
        return (100, 200, 300);
    }

    function returnMixed() internal pure returns (uint256, uint8, int256) {
        return (1000, 255, -50);
    }

    function returnWithZero() internal pure returns (uint256, uint256) {
        return (0, 42);
    }

    // =========================================================================
    // Unpack Tests
    // =========================================================================

    /// @dev Unpack two uint256: a=[10,10], b=[20,20]
    function test_unpack_two() public pure returns (uint256, uint256) {
        (uint256 a, uint256 b) = returnTwo();
        return (a, b);
    }

    /// @dev Unpack three uint256: a=[100,100], b=[200,200], c=[300,300]
    function test_unpack_three() public pure returns (uint256, uint256, uint256) {
        (uint256 a, uint256 b, uint256 c) = returnThree();
        return (a, b, c);
    }

    /// @dev Unpack mixed types: a=[1000,1000], b=[255,255], c=[-50,-50]
    function test_unpack_mixed() public pure returns (uint256, uint8, int256) {
        (uint256 a, uint8 b, int256 c) = returnMixed();
        return (a, b, c);
    }

    /// @dev Unpack with zero: a=[0,0], b=[42,42]
    function test_unpack_with_zero() public pure returns (uint256, uint256) {
        (uint256 a, uint256 b) = returnWithZero();
        return (a, b);
    }

    /// @dev Unpack and add: a+b = [30,30]
    function test_unpack_arithmetic() public pure returns (uint256) {
        (uint256 a, uint256 b) = returnTwo();
        return a + b;
    }

    /// @dev Partial unpack ignoring first: b=[20,20]
    function test_unpack_ignore_first() public pure returns (uint256) {
        (, uint256 b) = returnTwo();
        return b;
    }

    /// @dev Partial unpack ignoring second: a=[10,10]
    function test_unpack_ignore_second() public pure returns (uint256) {
        (uint256 a,) = returnTwo();
        return a;
    }

    /// @dev Unpack middle value: b=[200,200]
    function test_unpack_middle() public pure returns (uint256) {
        (, uint256 b,) = returnThree();
        return b;
    }
}
