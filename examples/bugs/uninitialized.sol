pragma solidity ^0.4.24;

contract Uninitialized{


    address destination;

    function transfer() public payable{
    
        destination.transfer(msg.value);
    }

}
