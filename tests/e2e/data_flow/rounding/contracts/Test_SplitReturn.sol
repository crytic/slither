// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Split-Direction Return Detection
/// @dev Mirrors the Balancer LinearMath._calcWrappedInPerBptOut bug:
/// the function has two return paths producing opposite rounding directions.
/// This pattern is invisible to the per-operation algebraic conflict rule
/// because there is no single point where UP and DOWN collide arithmetically.
contract Test_SplitReturn {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return (a + b - 1) / b;
    }

    /// @dev Two return paths return different SSA temps with opposite tags.
    /// Should be flagged by the split-direction rule.
    function buggy(uint256 x, uint256 denom, bool flag) external pure returns (uint256) {
        if (flag) {
            return divDown(x, denom);
        }
        return divUp(x, denom);
    }

    /// @dev Same direction on both paths — must NOT be flagged.
    function consistent(uint256 x, uint256 denom, bool flag) external pure returns (uint256) {
        if (flag) {
            return divDown(x, denom);
        }
        return divDown(x, denom + 1);
    }

    /// @dev Known gray area: a runtime-selected rounding direction is
    /// structurally indistinguishable from a wrong-direction bug at the
    /// IR level. Both produce two return-value temps with opposite tags.
    /// The split-direction rule will flag this; an auditor must verify
    /// whether the conditional choice is intentional (as here) or
    /// erroneous (as in the Balancer LinearMath case).
    function knownGrayArea_runtimeSelectedDirection(
        uint256 x,
        uint256 denom,
        bool roundUp
    ) external pure returns (uint256) {
        if (roundUp) {
            return divUp(x, denom);
        }
        return divDown(x, denom);
    }
}
