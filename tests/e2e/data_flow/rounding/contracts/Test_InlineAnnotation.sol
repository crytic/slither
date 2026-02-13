// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IMath {
    function mulDiv(uint256 a, uint256 b, uint256 c) external pure returns (uint256);
    function computeRate(uint256 x) external pure returns (uint256);
}

// Library with neutral names -- no directional hints in function names.
// Tag resolution must come entirely from inline round annotations.
library NeutralMath {
    function compute(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function scale(uint256 a, uint256 b, uint256 d) internal pure returns (uint256) {
        return (a * b) / d;
    }

    function combine(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    function reduce(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }
}

/// @title Test: Inline //@round annotation override
contract Test_InlineAnnotation {
    using NeutralMath for uint256;

    /// @dev Inline annotation tags mulDiv as DOWN
    function testBasic(
        IMath math,
        uint256 a,
        uint256 b,
        uint256 c
    ) external pure returns (uint256) {
        uint256 result = math.mulDiv(a, b, c); //@round mulDiv=DOWN
        return result;
    }

    /// @dev Inline annotation with invalid tag falls back to UNKNOWN
    function testOverrideNeutral(
        IMath math,
        uint256 x
    ) external pure returns (uint256) {
        uint256 result = math.computeRate(x); //@round computeRate=p
        return result;
    }

    /// @dev Multi-step chain with per-line annotations
    function testAnnotatedChain(
        uint256 x,
        uint256 y,
        uint256 z,
        uint256 d1,
        uint256 w,
        uint256 d2,
        uint256 v
    ) external pure returns (uint256) {
        uint256 step1 = x.compute(y); //@round compute=UP
        uint256 step2 = step1.scale(z, d1); //@round scale=DOWN
        uint256 step3 = step2.combine(w); //@round combine=DOWN
        uint256 step4 = step3.compute(d2); //@round compute=DOWN
        uint256 step5 = step4.reduce(v); //@round reduce=DOWN
        return step5;
    }

    /// @dev Single-line chain with all annotations on one line
    function testAnnotatedOneLine(
        uint256 x,
        uint256 y,
        uint256 z,
        uint256 d
    ) external pure returns (uint256) {
        return x.compute(y).scale(z, d).combine(z).reduce(d); //@round compute=UP, scale=DOWN, combine=DOWN, reduce=DOWN
    }

    /// @dev Malformed annotation -- should fall back to body analysis / UNKNOWN
    function testBadAnnotation(
        uint256 x,
        uint256 y
    ) external pure returns (uint256) {
        uint256 result = x.compute(y); //@round compute BROKEN
        return result;
    }
}
