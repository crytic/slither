// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Test: Multiple Paths to DOWN Tag
/// @dev Tests trace display when DOWN tag comes from different branches.
contract Test_MultipleDownPaths {
    function divDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    function mulDown(uint256 a, uint256 b) internal pure returns (uint256) {
        return a * b / 1e18;
    }

    /// @dev Both branches produce DOWN but from different sources
    function compute(uint256 x, uint256 y, bool useDiv) internal pure returns (uint256) {
        if (useDiv) {
            return divDown(x, y);
        } else {
            return mulDown(x, y);
        }
    }

    function foo (uint x, uint y) internal pure returns (uint) {
        return divDown(x, y);

    }

    /// @dev Calls compute - trace should show both possible DOWN sources
    function process(uint256 x, uint256 y, bool useDiv) external pure returns (uint256) {
        return compute(x, y, useDiv);
    }
}
