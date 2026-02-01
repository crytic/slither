// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Internal Call Operations
/// @dev Tests interval analysis for internal function calls
contract Test_InternalCall {
    // ============ Simple internal calls ============

    /// @dev Internal helper: returns input + 10
    function _addTen(uint256 x) internal pure returns (uint256) {
        return x + 10;
    }

    /// @dev Internal helper: returns input * 2
    function _double(uint256 x) internal pure returns (uint256) {
        return x * 2;
    }

    /// @dev Internal helper: returns constant 42
    function _constant42() internal pure returns (uint256) {
        return 42;
    }

    /// @dev Internal helper: returns a - b
    function _subtract(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }

    /// @dev Call internal function with constant: _addTen(5) = 15
    function test_internal_add_constant() public pure returns (uint256) {
        uint256 val = 5;
        return _addTen(val);
    }

    /// @dev Call internal function with parameter: _addTen(param)
    function test_internal_add_param(uint256 param) public pure returns (uint256) {
        return _addTen(param);
    }

    /// @dev Call internal constant function: _constant42() = 42
    function test_internal_constant() public pure returns (uint256) {
        return _constant42();
    }

    /// @dev Call internal function with two args: _subtract(10, 3) = 7
    function test_internal_two_args() public pure returns (uint256) {
        uint256 a = 10;
        uint256 b = 3;
        return _subtract(a, b);
    }

    // ============ Chained internal calls ============

    /// @dev Chained: _addTen(5) then _double -> (5 + 10) * 2 = 30
    function test_internal_chained() public pure returns (uint256) {
        uint256 val = 5;
        uint256 step1 = _addTen(val);
        return _double(step1);
    }

    /// @dev Nested: _double(_addTen(5)) -> (5 + 10) * 2 = 30
    function test_internal_nested() public pure returns (uint256) {
        uint256 val = 5;
        return _double(_addTen(val));
    }

    // ============ Internal call with expression ============

    /// @dev Internal result in expression: _addTen(3) + 5 = 18
    function test_internal_with_expression() public pure returns (uint256) {
        uint256 val = 3;
        uint256 result = _addTen(val);
        return result + 5;
    }

    /// @dev Internal with computed argument: _addTen(2 + 3) = 15
    function test_internal_computed_arg() public pure returns (uint256) {
        uint256 a = 2;
        uint256 b = 3;
        uint256 sum = a + b;
        return _addTen(sum);
    }

    // ============ Multiple internal calls ============

    /// @dev Multiple calls: _addTen(5) + _double(3) = 15 + 6 = 21
    function test_internal_multiple() public pure returns (uint256) {
        uint256 val1 = 5;
        uint256 val2 = 3;
        uint256 r1 = _addTen(val1);
        uint256 r2 = _double(val2);
        return r1 + r2;
    }

    // ============ Signed internal calls ============

    /// @dev Internal helper for signed: returns x + 10
    function _addTenSigned(int256 x) internal pure returns (int256) {
        return x + 10;
    }

    /// @dev Signed internal call: _addTenSigned(-5) = 5
    function test_internal_signed() public pure returns (int256) {
        int256 val = -5;
        return _addTenSigned(val);
    }
}
