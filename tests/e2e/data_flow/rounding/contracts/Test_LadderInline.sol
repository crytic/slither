// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Fixture: inline //@round annotation outranks name inference
contract Test_LadderInline {
    /// Name says UP; body floor-divides (would say DOWN)
    function divUp(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    /// Annotation forces DOWN despite the divUp name
    function annotated(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result = divUp(a, b); //@round divUp=DOWN
        return result;
    }

    /// Without an annotation the name allowlist wins → UP
    function unannotated(uint256 a, uint256 b) external pure returns (uint256) {
        uint256 result = divUp(a, b);
        return result;
    }
}
