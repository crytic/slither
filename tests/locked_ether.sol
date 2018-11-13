pragma solidity ^0.4.24;
contract Locked{

    function receive() payable public{
        require(msg.value > 0);
    }

}

contract Send{
    address owner = msg.sender;
    
    function withdraw() public{
        owner.transfer(address(this).balance);
    }
}

contract Unlocked is Locked, Send{

    function withdraw() public{
        super.withdraw();
    }

}

contract OnlyLocked is Locked{ }
