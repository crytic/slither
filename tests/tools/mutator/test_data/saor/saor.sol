// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.15;

contract SAORTest {
    function add(uint256 a, uint256 b) public pure returns (uint256) {
        return a + b;
    }

    function transfer(address from, address to, uint256 amount) public pure returns (bool) {
        return from != to && amount > 0;
    }

    function mixed(uint256 x, address y) public pure returns (bool) {
        return y != address(0) && x > 0;
    }

    function caller() public pure returns (uint256) {
        // Same-type args: should produce swap mutation
        uint256 result = add(1, 2);

        // Two address args of same type: should produce swap mutation
        transfer(address(0x1), address(0x2), 100);

        // Different-type args: should NOT produce swap mutation
        mixed(42, address(0x3));

        return result;
    }
}
