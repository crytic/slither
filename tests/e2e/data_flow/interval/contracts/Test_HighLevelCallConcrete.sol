// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: High Level Call Operations (Concrete contract type)
/// @dev Tests interval analysis for external calls to concrete contract types.
/// @dev Concrete calls are resolvable - interprocedural analysis is performed.

/// @dev Calculator implementation
contract Calculator {
    function add(uint256 a, uint256 b) external pure returns (uint256) {
        return a + b;
    }

    function sub(uint256 a, uint256 b) external pure returns (uint256) {
        return a - b;
    }

    function mul(uint256 a, uint256 b) external pure returns (uint256) {
        return a * b;
    }

    function double(uint256 x) external pure returns (uint256) {
        return x * 2;
    }

    function getConstant() external pure returns (uint256) {
        return 42;
    }
}

/// @title Test contract for high-level calls to concrete contract
contract Test_HighLevelCallConcrete {
    Calculator public calc;

    constructor(Calculator _calc) {
        calc = _calc;
    }

    // ============ Simple concrete calls ============

    /// @dev Concrete call with constants: calc.add(5, 10) = 15
    /// @dev Expected: result ∈ [15, 15] (interprocedural)
    function test_concrete_add_constants() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        return calc.add(a, b);
    }

    /// @dev Concrete call with parameter
    /// @dev Expected: param back-propagated from add constraints
    function test_concrete_add_param(uint256 param) public view returns (uint256) {
        uint256 b = 10;
        return calc.add(param, b);
    }

    /// @dev Concrete call returning constant: calc.getConstant() = 42
    /// @dev Expected: result ∈ [42, 42] (interprocedural)
    function test_concrete_constant() public view returns (uint256) {
        return calc.getConstant();
    }

    // ============ Chained concrete calls ============

    /// @dev Chained: calc.add(5, 10) then calc.double(result)
    /// @dev Expected: step1 ∈ [15, 15], result ∈ [30, 30]
    function test_concrete_chained() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 step1 = calc.add(a, b);
        return calc.double(step1);
    }

    // ============ Concrete call with local computation ============

    /// @dev Concrete call result used in local computation
    /// @dev Expected: extResult ∈ [15, 15], final ∈ [115, 115]
    function test_concrete_with_local_computation() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 extResult = calc.add(a, b);
        uint256 localAdd = 100;
        return extResult + localAdd;
    }

    /// @dev Local computation then concrete call
    /// @dev Expected: sum ∈ [15, 15], result ∈ [30, 30]
    function test_local_then_concrete() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 sum = a + b;
        return calc.double(sum);
    }

    // ============ Multiple concrete calls ============

    /// @dev Multiple concrete calls combined
    /// @dev Expected: r1 ∈ [15, 15], r2 ∈ [50, 50], result ∈ [65, 65]
    function test_multiple_concrete_calls() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 r1 = calc.add(a, b);
        uint256 r2 = calc.mul(a, b);
        return r1 + r2;
    }

    // ============ Subtraction concrete call ============

    /// @dev Concrete subtraction: calc.sub(10, 3) = 7
    /// @dev Expected: result ∈ [7, 7]
    function test_concrete_sub() public view returns (uint256) {
        uint256 a = 10;
        uint256 b = 3;
        return calc.sub(a, b);
    }
}
