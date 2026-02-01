// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Type Conversion Operations
/// @dev Tests interval analysis for type casts (widening and narrowing)
contract Test_TypeConversion {
    // ============ Widening (small to large) ============

    /// @dev uint8 to uint256: value preserved, range [0, 255] -> [0, 255]
    function test_uint8_to_uint256(uint8 x) public pure returns (uint256) {
        return uint256(x);
    }

    /// @dev uint16 to uint256
    function test_uint16_to_uint256(uint16 x) public pure returns (uint256) {
        return uint256(x);
    }

    /// @dev int8 to int256: sign extended
    function test_int8_to_int256(int8 x) public pure returns (int256) {
        return int256(x);
    }

    /// @dev Constant widening: 10 (uint8) -> 10 (uint256)
    function test_constant_widen() public pure returns (uint256) {
        uint8 a = 10;
        return uint256(a);
    }

    // ============ Narrowing (large to small) ============

    /// @dev uint256 to uint8: truncates to [0, 255]
    function test_uint256_to_uint8(uint256 x) public pure returns (uint8) {
        return uint8(x);
    }

    /// @dev uint256 to uint16: truncates to [0, 65535]
    function test_uint256_to_uint16(uint256 x) public pure returns (uint16) {
        return uint16(x);
    }

    /// @dev int256 to int8: truncates
    function test_int256_to_int8(int256 x) public pure returns (int8) {
        return int8(x);
    }

    /// @dev Constant narrowing: 1000 (uint256) -> truncated (uint8)
    function test_constant_narrow() public pure returns (uint8) {
        uint256 a = 1000;
        return uint8(a);  // 1000 % 256 = 232
    }

    // ============ Signed/Unsigned conversions ============

    /// @dev uint256 to int256: reinterpret bits
    function test_uint_to_int(uint256 x) public pure returns (int256) {
        return int256(x);
    }

    /// @dev int256 to uint256: reinterpret bits
    function test_int_to_uint(int256 x) public pure returns (uint256) {
        return uint256(x);
    }

    /// @dev Negative constant to uint: wraps
    function test_negative_to_uint() public pure returns (uint256) {
        int256 a = -1;
        return uint256(a);  // max uint256
    }

    // ============ Same size conversions ============

    /// @dev uint128 to int128
    function test_uint128_to_int128(uint128 x) public pure returns (int128) {
        return int128(x);
    }

    /// @dev int128 to uint128
    function test_int128_to_uint128(int128 x) public pure returns (uint128) {
        return uint128(x);
    }
}
