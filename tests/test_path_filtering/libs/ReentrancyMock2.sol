// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.6.12;

contract ReentrancyMock2 {
    mapping(address => uint256) public userBalances2;

    function withdraw2() external {
        uint256 userBalance = userBalances2[msg.sender];
        require(userBalance > 0);
        (bool success, ) = msg.sender.call{value: userBalance}("");
        require(success);
        userBalances2[msg.sender] = 0;
    }
}
