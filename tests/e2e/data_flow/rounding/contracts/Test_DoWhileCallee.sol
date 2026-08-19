// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: node-order-dependent callee (do-while condition calls divUp)
/// @dev Slither lists the IFLOOP condition node BEFORE the loop-body node that
///      defines `t`, but the condition executes AFTER the body. The nested
///      fixpoint propagates t = DOWN into the condition, so divUp(t, t) is a
///      both-DOWN division inconsistency. The old single-pass callee walk
///      processed nodes in list order, evaluated the condition with `t` still
///      untagged, and missed the finding.
contract Test_DoWhileCallee {
    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    function helper(uint256 p, uint256 q) internal pure returns (uint256) {
        uint256 t = 0;
        do {
            t = p / q;
        } while (divUp(t, t) > 0);
        return t;
    }

    function caller(uint256 x, uint256 y) external pure returns (uint256) {
        uint256 result = helper(x, y);
        return result;
    }
}
