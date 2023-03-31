pragma solidity ^0.6.12;

contract FakeFallback {
    mapping(address => uint) public contributions;
    address payable public owner;

    constructor() public {
        owner = payable(msg.sender);
        contributions[msg.sender] = 1000 * (1 ether);
    }

    function fallback() public payable {
        contributions[msg.sender] += msg.value;
    }

    function receive() public payable {
        contributions[msg.sender] += msg.value;
    }
}

contract Fallback is FakeFallback {
    receive() external payable {
        contributions[msg.sender] += msg.value;
    }

    fallback() external payable {
        contributions[msg.sender] += msg.value;
    }
}
