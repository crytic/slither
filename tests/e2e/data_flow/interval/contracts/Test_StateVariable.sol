// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: State Variables
/// @dev State variables have unknown values when read (full type range)
///      because they persist across function calls
contract Test_StateVariable {
    // =========================================================================
    // State Variable Declarations
    // =========================================================================

    uint256 public stateUint256;
    uint8 public stateUint8;
    int256 public stateInt256;
    bool public stateBool;
    address public stateAddress;
    uint128 public stateUint128;

    // =========================================================================
    // Write Tests - Assignments track precise values
    // =========================================================================

    /// @dev Write constant to uint256: expected [42, 42]
    function test_write_uint256() public {
        stateUint256 = 42;
    }

    /// @dev Write max to uint8: expected [255, 255]
    function test_write_uint8() public {
        stateUint8 = 255;
    }

    /// @dev Write negative to int256: expected [-100, -100]
    function test_write_int256() public {
        stateInt256 = -100;
    }

    /// @dev Write true to bool: expected [1, 1]
    function test_write_bool() public {
        stateBool = true;
    }

    // =========================================================================
    // Read-Write Patterns
    // =========================================================================

    /// @dev Read then write: new value should be [100, 100]
    function test_read_then_write() public returns (uint256) {
        uint256 old = stateUint256;
        stateUint256 = 100;
        return old;
    }

    /// @dev Increment: result should be [1, max] with overflow check
    function test_increment() public {
        stateUint256 = stateUint256 + 1;
    }

    /// @dev State * 2: overflow check narrows input to [0, max/2]
    function test_multiply_state() public view returns (uint256) {
        return stateUint256 * 2;
    }

    /// @dev Add two state vars: result is full range
    function test_add_states() public view returns (uint256) {
        return stateUint256 + stateUint128;
    }
}
