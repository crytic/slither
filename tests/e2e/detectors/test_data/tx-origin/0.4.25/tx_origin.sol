//pragma solidity ^0.4.24;

contract TxOrigin {

    address owner;

    constructor() { owner = msg.sender; }

    function bug0() {
        require(tx.origin == owner);
    }

    function bug2() {
        if (tx.origin != owner) {
            revert();
        }
    }

    function legit0(){
        require(tx.origin == msg.sender);
    }
    
    function legit1(){
        tx.origin.transfer(this.balance);
    }
}
