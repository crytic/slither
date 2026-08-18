// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Minimal fixture for data-flow engine tests
contract EngineFixture {
    function add(uint256 seeded, uint256 unseeded) public pure returns (uint256) {
        uint256 result = seeded + unseeded;
        return result;
    }
}
