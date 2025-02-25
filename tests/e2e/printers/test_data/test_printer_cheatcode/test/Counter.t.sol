// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "forge-std/Test.sol";
import "../src/Counter.sol";

contract CounterTest is Test {
    Counter public counter;

    address public alice = address(0x42);
    address public bob = address(0x43);

    function difficulty(uint256 value) public {
        // empty
    }

    function setUp() public {
        counter = new Counter();
        counter.setNumber(0);

        vm.deal(alice, 1 ether);
        vm.deal(bob, 2 ether);

        difficulty(1);
    }

    function testIncrement() public {
        vm.prank(alice);
        counter.increment();
        assertEq(counter.number(), 1);

        vm.prank(bob);
        counter.increment();
        assertEq(counter.number(), 2);
    }
}
