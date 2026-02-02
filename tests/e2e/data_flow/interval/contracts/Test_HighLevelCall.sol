// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: High Level Call Operations (Interface-based)
/// @dev Tests interval analysis for external contract calls through interfaces.
/// @dev Interface calls are unresolvable - return values are unconstrained.

/// @dev Simple calculator interface
interface ICalculator {
    function add(uint256 a, uint256 b) external pure returns (uint256);
    function sub(uint256 a, uint256 b) external pure returns (uint256);
    function mul(uint256 a, uint256 b) external pure returns (uint256);
    function double(uint256 x) external pure returns (uint256);
    function getConstant() external pure returns (uint256);
}

/// @title Test contract for high-level calls through interface
contract Test_HighLevelCall {
    ICalculator public calculator;

    constructor(address _calculator) {
        calculator = ICalculator(_calculator);
    }

    // ============ Simple external calls ============

    /// @dev External call with constants: calculator.add(5, 10)
    /// @dev Expected: result unconstrained (interface call)
    function test_external_add_constants() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        return calculator.add(a, b);
    }

    /// @dev External call with parameter
    /// @dev Expected: param unconstrained, result unconstrained
    function test_external_add_param(uint256 param) public view returns (uint256) {
        uint256 b = 10;
        return calculator.add(param, b);
    }

    /// @dev External call returning constant
    /// @dev Expected: result unconstrained (cannot resolve interface)
    function test_external_constant() public view returns (uint256) {
        return calculator.getConstant();
    }

    // ============ Chained external calls ============

    /// @dev Chained: calculator.add(5, 10) then calculator.double(result)
    /// @dev Expected: step1 unconstrained, result unconstrained
    function test_external_chained() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 step1 = calculator.add(a, b);
        return calculator.double(step1);
    }

    // ============ External call with local computation ============

    /// @dev External call result used in local computation
    /// @dev Expected: extResult unconstrained, overflow-constrained by + 100
    function test_external_with_local_computation() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 extResult = calculator.add(a, b);
        uint256 localAdd = 100;
        return extResult + localAdd;
    }

    /// @dev Local computation then external call
    /// @dev Expected: sum ∈ [15, 15], result unconstrained
    function test_local_then_external() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 sum = a + b;
        return calculator.double(sum);
    }

    // ============ Multiple external calls ============

    /// @dev Multiple external calls combined
    /// @dev Expected: r1, r2 unconstrained, result unconstrained
    function test_multiple_external_calls() public view returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        uint256 r1 = calculator.add(a, b);
        uint256 r2 = calculator.mul(a, b);
        return r1 + r2;
    }

    // ============ External call with address parameter ============

    /// @dev Call on dynamic address
    /// @dev Expected: result unconstrained
    function test_external_dynamic_address(address calc) public pure returns (uint256) {
        uint256 a = 5;
        uint256 b = 10;
        return ICalculator(calc).add(a, b);
    }
}
