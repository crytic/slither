// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Struct Operations
/// @dev Tests struct field read/write operations
contract Test_Struct {
    struct User {
        uint256 id;
        uint256 balance;
    }

    struct Nested {
        uint256 value;
        User user;
    }

    User public user;
    Nested public nested;

    // =========================================================================
    // Simple Struct Operations
    // =========================================================================

    /// @dev Write constant to struct field
    function test_write_field() public {
        user.id = 42;
    }

    /// @dev Write multiple fields
    function test_write_multiple_fields() public {
        user.id = 1;
        user.balance = 100;
    }

    /// @dev Read struct field
    function test_read_field() public view returns (uint256) {
        return user.balance;
    }

    /// @dev Write then read same field
    function test_write_read_field() public returns (uint256) {
        user.balance = 500;
        return user.balance;
    }

    /// @dev Set value then add to it
    function test_set_then_add() public returns (uint256) {
        user.balance = 100;
        user.balance = user.balance + 50;
        return user.balance;
    }

    // =========================================================================
    // Memory Struct
    // =========================================================================

    /// @dev Create memory struct and write
    function test_memory_struct() public pure returns (uint256) {
        User memory u;
        u.id = 10;
        u.balance = 200;
        return u.balance;
    }

    /// @dev Struct as parameter
    function test_struct_param(User memory u) public pure returns (uint256) {
        return u.balance;
    }

    // =========================================================================
    // Nested Struct
    // =========================================================================

    /// @dev Write to nested struct
    function test_nested_write() public {
        nested.value = 999;
        nested.user.id = 1;
        nested.user.balance = 50;
    }

    /// @dev Read from nested struct
    function test_nested_read() public view returns (uint256) {
        return nested.user.balance;
    }
}
