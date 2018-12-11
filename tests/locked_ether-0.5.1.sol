pragma solidity ^0.5.0;
contract Locked{

    function receive() payable public{
        require(msg.value > 0);
    }

}

contract Send{
    address payable owner = msg.sender;
    
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
