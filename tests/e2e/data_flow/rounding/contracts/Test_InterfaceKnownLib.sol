// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: bodyless interface call resolves via name-only known-library fallback
/// @dev The builtin table keys mulDiv under contract "FullMath"; the interface
///      is named IFullMath so an exact (contract, function) match is impossible.
///      A bodyless HighLevelCall target must resolve to None so the lookup takes
///      the function-name-only fallback (DOWN). Without the table, the callee is
///      unresolvable and the result defaults to NEUTRAL.
interface IFullMath {
    function mulDiv(uint256 a, uint256 b, uint256 d) external pure returns (uint256);
}

contract Test_InterfaceKnownLib {
    function caller(
        IFullMath math,
        uint256 x,
        uint256 y,
        uint256 d
    ) external pure returns (uint256) {
        uint256 result = math.mulDiv(x, y, d);
        return result;
    }
}
