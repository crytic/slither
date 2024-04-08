// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/Vault.sol";

contract VaultTest is Test {

    Vault public vault;

    address public alice = address(0x42);

    function broadcast() pure public {}

    function setUp() public {
        vm.prank(alice);
        vm.deal(alice, 1000 ether);

        uint256 value = 123;

        vm.warp(1641070800);
        vm.roll(100);
        vm.fee(25 gwei);

        // Not a cheatcode
        broadcast();
    }

    function test_deal() public {

    }
}
