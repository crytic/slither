pragma solidity ^0.4.24;

contract Uninitialized{

    address destination;

    function transfer() payable public{
        destination.transfer(msg.value);
    }

}
