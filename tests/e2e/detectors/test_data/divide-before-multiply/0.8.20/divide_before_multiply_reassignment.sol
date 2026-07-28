// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

/// Regression coverage for the `divide-before-multiply` reassignment-kill fix.
/// `_explore`'s Assignment handler in `divide_before_multiply.py` propagates
/// taint from `rvalue` to `lvalue` when `rvalue` is itself division-tainted,
/// but never CLEARS `divisions[lvalue]` when the rvalue is a clean value.
/// So a variable that was previously the result of a division and is then
/// fully overwritten with an unrelated value still keeps its division taint,
/// and the next multiplication using it fires.
///
/// Expected output after fix: exactly one finding, for `genuineDivThenMul`
/// (the tripwire confirming the detector still catches the real bug).

contract DivideBeforeMultiplyTest {
    // FP class (fix): variable reassigned to a clean value before being multiplied.
    function safeReassign(uint256 x, uint256 y, uint256 z) public pure returns (uint256) {
        uint256 a = x / y;
        a = z;             // `a` no longer holds x/y
        return a * 100;    // multiplies z, not a division result
    }

    // FP class (fix): chained reassignment through a temporary.
    function safeChainedReassign(uint256 x, uint256 y, uint256 z) public pure returns (uint256) {
        uint256 a = x / y;
        uint256 t = z;
        a = t;             // taint should not propagate from a clean rvalue
        return a * 100;
    }

    // Tripwire — the real divide-then-multiply pattern. Must still fire.
    function genuineDivThenMul(uint256 x, uint256 y, uint256 z) public pure returns (uint256) {
        uint256 a = x / y;
        return a * z;      // genuine precision loss path
    }
}
