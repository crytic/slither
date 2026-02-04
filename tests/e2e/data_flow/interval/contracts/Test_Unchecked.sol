// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Unchecked Arithmetic Operations
/// @dev Tests overflow detection in unchecked blocks
contract Test_Unchecked {
    /// @dev Addition in unchecked block - can overflow
    /// Input: a, b [0, 2^256-1], Output: result can overflow
    function test_unchecked_add(uint256 a, uint256 b) public pure returns (uint256 result) {
        unchecked {
            result = a + b;
        }
    }

    /// @dev Subtraction in unchecked block - can underflow
    /// Input: a, b [0, 2^256-1], Output: result can underflow
    function test_unchecked_sub(uint256 a, uint256 b) public pure returns (uint256 result) {
        unchecked {
            result = a - b;
        }
    }

    /// @dev Multiplication in unchecked block - can overflow
    /// Input: a, b [0, 2^256-1], Output: result can overflow
    function test_unchecked_mul(uint256 a, uint256 b) public pure returns (uint256 result) {
        unchecked {
            result = a * b;
        }
    }

    /// @dev Checked addition - no overflow possible (reverts instead)
    /// Input: a, b [0, 2^256-1], Output: safe result
    function test_checked_add(uint256 a, uint256 b) public pure returns (uint256 result) {
        result = a + b;
    }

    /// @dev Mixed: checked then unchecked
    function test_mixed(uint256 a, uint256 b) public pure returns (uint256 unsafe) {

        require(a < 100);
        require(b < 100);
        uint safe = a + b;  // checked
        unchecked {
            unsafe = a + b;  // unchecked
        }
    }
}
