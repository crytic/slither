// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ClaudeTest
 * @dev A simple contract with intentional vulnerabilities for testing Claude detector
 */
contract ClaudeTest {
    mapping(address => uint256) public balances;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Potential reentrancy vulnerability
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // State change after external call - reentrancy risk
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        balances[msg.sender] -= amount;
    }

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // Missing access control
    function setOwner(address newOwner) external {
        owner = newOwner;
    }
}
