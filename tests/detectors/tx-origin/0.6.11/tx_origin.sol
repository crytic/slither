// pragma solidity ^0.5.0;

contract TxOrigin {

    address payable owner;

    constructor() public{ owner = msg.sender; }

    function bug0() public{
        require(tx.origin == owner);
    }

    function bug2() public{
        if (tx.origin != owner) {
            revert();
        }
    }

    function legit0() public{
        require(tx.origin == msg.sender);
    }
    
    function legit1() public{
        tx.origin.transfer(address(this).balance);
    }
}
