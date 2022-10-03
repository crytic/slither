// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract ReentrancyMock3 {
    mapping(address => uint256) public userBalances3;

    function withdraw3() external {
        uint256 userBalance = userBalances3[msg.sender];
        require(userBalance > 0);
        (bool success, ) = msg.sender.call{value: userBalance}("");
        require(success);
        userBalances3[msg.sender] = 0;
    }
}
