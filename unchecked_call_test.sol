// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UncheckedCallTest {
    function testUncheckedCall(address payable recipient, uint256 amount) public payable {
        recipient.call{value: amount}("");
    }
}
