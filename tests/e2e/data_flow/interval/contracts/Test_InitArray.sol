// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: InitArray (array literal initialization)
/// @dev Tests array initialization with literal values [1, 2, 3]
contract Test_InitArray {

    // =========================================================================
    // Phase 1: Isolated - constant initialization
    // =========================================================================

    /// @dev Init uint256 array with constants (second element is plain Constant)
    /// Expected: arr[0] unconstrained (type conversion), arr[1]=[2,2]
    function test_constants_uint256() public pure returns (uint256) {
        uint256[2] memory arr = [uint256(1), 2];
        return arr[1];
    }

    /// @dev Init uint256 array with three constants
    /// Expected: arr[1]=[20,20], arr[2]=[30,30]
    function test_three_constants() public pure returns (uint256, uint256) {
        uint256[3] memory arr = [uint256(10), 20, 30];
        return (arr[1], arr[2]);
    }

    // =========================================================================
    // Phase 2: Variable initialization
    // =========================================================================

    /// @dev Init array with parameter variables
    /// Expected: arr[0]=[0,2^256-1], arr[1]=[0,2^256-1]
    function test_variables(uint256 x, uint256 y) public pure returns (uint256) {
        uint256[2] memory arr = [x, y];
        return arr[0];
    }

    /// @dev Init array with mixed constant and variable
    /// Expected: arr[0] via TypeConversion, arr[1]=[0,2^256-1]
    function test_mixed(uint256 x) public pure returns (uint256) {
        uint256[2] memory arr = [uint256(42), x];
        return arr[1];
    }

    // =========================================================================
    // Phase 3: Read after init (propagation through Index)
    // =========================================================================

    /// @dev Init then read - verifies element propagation
    /// Expected: b=[20,20] (constant propagated through InitArray then Index)
    function test_read_constant_element() public pure returns (uint256) {
        uint256[3] memory arr = [uint256(10), 20, 30];
        uint256 b = arr[1];
        return b;
    }

    /// @dev Init then use in arithmetic
    /// Expected: result constrained by arr[1]+arr[2] = 20+30 = [50,50]
    function test_arithmetic_after_init() public pure returns (uint256) {
        uint256[3] memory arr = [uint256(10), 20, 30];
        uint256 result = arr[1] + arr[2];
        return result;
    }
}
