// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Engine fixture: loop requiring fixpoint convergence
contract EngineLoop {
    function loop(uint256 n) public pure returns (uint256) {
        uint256 acc = 0;
        for (uint256 i = 0; i < n; i++) {
            acc = acc + 1;
        }
        return acc;
    }
}
