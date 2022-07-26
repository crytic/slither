// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.12;

contract ReentrancyMock1 {
    mapping(address => uint256) public userBalances1;

    function withdraw1() external {
        uint256 userBalance = userBalances1[msg.sender];
        require(userBalance > 0);
        (bool success, ) = msg.sender.call{value: userBalance}("");
        require(success);
        userBalances1[msg.sender] = 0;
    }
}
