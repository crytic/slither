pragma solidity ^0.4.24;

contract C{

    function i_am_a_backdoor() public{
        selfdestruct(msg.sender);
    }

}
