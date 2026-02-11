// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Math library with rounding-aware operations
/// @dev Mirrors real-world SafeMath/FixedPoint libraries used with `using ... for uint256`
library MathLib {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }

    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    function mulDown(uint256 a, uint256 b, uint256 d) internal pure returns (uint256) {
        return (a * b) / d;
    }

    function mulUp(uint256 a, uint256 b, uint256 d) internal pure returns (uint256) {
        return (a * b + d - 1) / d;
    }
}

/// @title Test: Library Call Tag Propagation
/// @dev Tests rounding tags flow correctly through `using Library for uint256` calls
contract Test_LibraryCall {
    using MathLib for uint256;

    /// @dev divDown via library call: should be DOWN
    function test_lib_divDown(uint256 x, uint256 y) external pure returns (uint256) {
        return x.divDown(y);
    }

    /// @dev divUp via library call: should be UP
    function test_lib_divUp(uint256 x, uint256 y) external pure returns (uint256) {
        return x.divUp(y);
    }

    /// @dev DOWN.sub(NEUTRAL): DOWN - NEUTRAL -> inverted NEUTRAL -> DOWN
    function test_lib_sub_down_neutral(
        uint256 x,
        uint256 y,
        uint256 z
    ) external pure returns (uint256) {
        uint256 down = x.divDown(y);
        return down.sub(z);
    }

    /// @dev NEUTRAL.sub(DOWN): NEUTRAL - DOWN -> inverted UP -> UP
    function test_lib_sub_neutral_down(
        uint256 x,
        uint256 y,
        uint256 z
    ) external pure returns (uint256) {
        uint256 down = x.divDown(y);
        return z.sub(down);
    }

    /// @dev UP.add(NEUTRAL): UP + NEUTRAL -> UP
    function test_lib_add_up_neutral(
        uint256 x,
        uint256 y,
        uint256 z
    ) external pure returns (uint256) {
        uint256 up = x.divUp(y);
        return up.add(z);
    }

    /// @dev Chain: divUp then mulDown -> mixed directions
    function test_lib_chain(
        uint256 x,
        uint256 y,
        uint256 z,
        uint256 d
    ) external pure returns (uint256) {
        uint256 up = x.divUp(y);
        return up.mulDown(z, d);
    }
}
