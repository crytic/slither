// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Internal Dynamic Call (function pointers)
/// @dev Tests interval analysis with function-type variables
contract Test_InternalDynamicCall {
    /// @dev Call a function pointer that returns uint256
    /// Expected: result is unconstrained [0, max] since target is unknown at compile time
    function test_simple_function_pointer(uint256 x) public pure returns (uint256) {
        function(uint256) pure returns (uint256) fn = identity;
        uint256 result = fn(x);
        return result;
    }

    /// @dev Call a function pointer selected at runtime
    /// Expected: result is unconstrained [0, max]
    function test_conditional_function_pointer(uint256 x, bool useDouble) public pure returns (uint256) {
        function(uint256) pure returns (uint256) fn;
        if (useDouble) {
            fn = double;
        } else {
            fn = identity;
        }
        uint256 result = fn(x);
        return result;
    }

    /// @dev Function pointer returning multiple values
    /// Expected: both return values are unconstrained [0, max]
    function test_tuple_return_pointer(uint256 x) public pure returns (uint256, uint256) {
        function(uint256) pure returns (uint256, uint256) fn = splitValue;
        (uint256 a, uint256 b) = fn(x);
        return (a, b);
    }

    /// @dev Chain of function pointer calls
    /// Expected: final result is unconstrained [0, max]
    function test_chained_pointer_calls(uint256 x) public pure returns (uint256) {
        function(uint256) pure returns (uint256) fn1 = double;
        function(uint256) pure returns (uint256) fn2 = identity;
        uint256 intermediate = fn1(x);
        uint256 result = fn2(intermediate);
        return result;
    }

    // Helper functions for the function pointers
    function identity(uint256 x) internal pure returns (uint256) {
        return x;
    }

    function double(uint256 x) internal pure returns (uint256) {
        return x * 2;
    }

    function splitValue(uint256 x) internal pure returns (uint256, uint256) {
        return (x / 2, x - x / 2);
    }
}
