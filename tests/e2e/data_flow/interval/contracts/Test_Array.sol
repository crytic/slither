// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Array Operations
/// @dev Tests array declarations and assignments
contract Test_Array {
    // State variable arrays
    uint256[] public dynamicArray;
    uint256[3] public fixedArray;
    uint256[3] public initializedArray = [1, 2, 3];

    // =========================================================================
    // Array as Parameter
    // =========================================================================

    // / @dev Read from array parameter
    function test_param_read(uint256[] memory arr) public pure returns (uint256) {
        return arr[0];
    }

    /// @dev Write to array parameter
    function test_param_write(uint256[] memory arr) public pure returns (uint256) {
        arr[0] = 42;
        return arr[0];
    }

    // =========================================================================
    // State Variable Arrays
    // =========================================================================

    /// @dev Write to state array
    function test_state_write() public {
        dynamicArray.push(100);
    }

    /// @dev Multiple pushes to state array
    function test_state_multi_push() public {
        dynamicArray.push(10);
        dynamicArray.push(20);
        dynamicArray.push(30);
    }

    /// @dev Read from state array
    function test_state_read() public view returns (uint256) {
        return dynamicArray[0];
    }

    /// @dev Write to fixed state array
    function test_fixed_state_write() public {
        fixedArray[0] = 10;
        fixedArray[1] = 20;
    }

    /// @dev Read from fixed state array
    function test_fixed_state_read() public view returns (uint256) {
        return fixedArray[0];
    }

    // =========================================================================
    // Initialized Arrays
    // =========================================================================

    /// @dev Read from initialized array
    function test_initialized_array_read() public view returns (uint256) {
        return initializedArray[0];
    }

    /// @dev Read multiple from initialized array
    function test_initialized_array_sum() public view returns (uint256) {
        return initializedArray[0] + initializedArray[1] + initializedArray[2];
    }
}
