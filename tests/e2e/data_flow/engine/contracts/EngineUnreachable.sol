// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Engine fixture: statement after return is CFG-unreachable
/// @dev Slither links post-revert code into the CFG, so a trailing
///      statement after `return` is used to get a truly father-less node.
contract EngineUnreachable {
    function unreachable(uint256 x) public pure returns (uint256) {
        return x;
        x = x + 1;
    }
}
