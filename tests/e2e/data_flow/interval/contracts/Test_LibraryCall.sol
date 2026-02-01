// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Math Library for testing
/// @dev Simple library with arithmetic operations
library MathLib {
    /// @dev Add two numbers
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    /// @dev Subtract two numbers
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }

    /// @dev Multiply two numbers
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        return a * b;
    }

    /// @dev Double a number
    function double(uint256 a) internal pure returns (uint256) {
        return a * 2;
    }

    /// @dev Return constant
    function constant42() internal pure returns (uint256) {
        return 42;
    }
}

/// @title Test: Library Call Operations
/// @dev Tests interval analysis for library function calls
contract Test_LibraryCall {
    using MathLib for uint256;

    // ============ Direct library calls ============

    /// @dev Library add with constants: 5 + 3 = 8 -> [0, max] (library result)
    function test_lib_add_constants() public pure returns (uint256) {
        uint256 val1 = 5;
        uint256 val2 = 3;
        return MathLib.add(val1, val2);
    }

    /// @dev Library sub with constants: 10 - 3 = 7 -> [0, max] (library result)
    function test_lib_sub_constants() public pure returns (uint256) {
        uint256 val1 = 10;
        uint256 val2 = 3;
        return MathLib.sub(val1, val2);
    }

    /// @dev Library mul with constants: 4 * 5 = 20 -> [0, max] (library result)
    function test_lib_mul_constants() public pure returns (uint256) {
        uint256 val1 = 4;
        uint256 val2 = 5;
        return MathLib.mul(val1, val2);
    }

    /// @dev Library with parameters: add(x, y) -> [0, max]
    function test_lib_add_params(uint256 param1, uint256 param2) public pure returns (uint256) {
        return MathLib.add(param1, param2);
    }

    /// @dev Library constant function: returns 42 -> [0, max] (library result)
    function test_lib_constant() public pure returns (uint256) {
        return MathLib.constant42();
    }

    // ============ Using syntax ============

    /// @dev Using syntax: val.double() -> [0, max]
    function test_using_double(uint256 val) public pure returns (uint256) {
        return val.double();
    }

    /// @dev Using syntax with constant: 5.double() -> [0, max] (library result)
    function test_using_double_constant() public pure returns (uint256) {
        uint256 val = 5;
        return val.double();
    }

    // ============ Chained library calls ============

    /// @dev Chained: add(5, 3) then double -> [0, max] (library result)
    function test_lib_chained() public pure returns (uint256) {
        uint256 val1 = 5;
        uint256 val2 = 3;
        uint256 sum = MathLib.add(val1, val2);
        return MathLib.double(sum);
    }

    /// @dev Library result used in expression: add(2, 3) + 10 -> [10, max]
    function test_lib_with_expression() public pure returns (uint256) {
        uint256 val1 = 2;
        uint256 val2 = 3;
        uint256 libResult = MathLib.add(val1, val2);
        return libResult + 10;
    }
}
