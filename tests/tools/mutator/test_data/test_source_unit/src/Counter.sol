// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.15;

contract Counter {
    uint256 public number;
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    function setNumber(uint256 newNumber) public {
        number = newNumber;
    }

    function increment() public {
        number++;
    }

    function restrictedIncrement() public onlyOwner {
        number++;
    }
}
