// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Mapping Operations
/// @dev Tests mapping read/write operations
contract Test_Mapping {
    mapping(address => uint256) public balances;
    mapping(uint256 => uint256) public values;
    mapping(address => mapping(uint256 => uint256)) public nested;

    // =========================================================================
    // Simple Mapping Operations
    // =========================================================================

    /// @dev Write constant to mapping
    function test_write_constant(address user) public {
        balances[user] = 100;
    }

    /// @dev Read from mapping
    function test_read(address user) public view returns (uint256) {
        return balances[user];
    }

    /// @dev Write then read same key
    function test_write_read(address user) public returns (uint256) {
        balances[user] = 42;
        return balances[user];
    }

    // =========================================================================
    // Uint Key Mapping
    // =========================================================================

    /// @dev Write with uint key
    function test_uint_key_write(uint256 key) public {
        values[key] = 200;
    }

    /// @dev Read with uint key
    function test_uint_key_read(uint256 key) public view returns (uint256) {
        return values[key];
    }

    // =========================================================================
    // Nested Mapping
    // =========================================================================

    /// @dev Write to nested mapping
    function test_nested_write(address user, uint256 id) public {
        nested[user][id] = 500;
    }

    /// @dev Read from nested mapping
    function test_nested_read(address user, uint256 id) public view returns (uint256) {
        return nested[user][id];
    }

    // =========================================================================
    // Arithmetic with Mapping Values
    // =========================================================================

    /// @dev Increment mapping value
    function test_increment(address user) public {
        balances[user] = balances[user] + 10;
    }
}
