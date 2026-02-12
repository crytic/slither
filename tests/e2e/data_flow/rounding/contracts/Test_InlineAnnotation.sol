// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IMath {
    function mulDiv(uint256 a, uint256 b, uint256 c) external pure returns (uint256);
    function computeRate(uint256 x) external pure returns (uint256);
}

/// @title Test: Inline //@round annotation override
contract Test_InlineAnnotation {

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

    /// @dev Inline annotation tags computeRate as UP
    function testOverrideNeutral(
        IMath math,
        uint256 x
    ) external pure returns (uint256) {
        uint256 result = math.computeRate(x); //@round computeRate=p
        return result;
    }

 
}
