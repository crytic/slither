// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.12;

contract ReentrancyMock {
    mapping(address => uint256) public userBalances;
    
    function withdraw() external {
        uint256 userBalance = userBalances[msg.sender];
        require(userBalance > 0);
        (bool success, ) = msg.sender.call{value: userBalance}("");
        require(success);
        userBalances[msg.sender] = 0;
    }
}
