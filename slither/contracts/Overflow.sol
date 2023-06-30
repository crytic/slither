// SPDX-License-Identifier:MIT

pragma solidity 0.8.18;

contract IntegerOverflowMinimal {
    mapping(address => uint256) public balanceOf;
    uint256 constant PRICE_PER_TOKEN = 1 ether;

    function buy(uint256 numTokens) public payable {
        require(msg.value == numTokens);

        balanceOf[msg.sender] += numTokens;
    }
}

