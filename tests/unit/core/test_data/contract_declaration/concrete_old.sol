pragma solidity ^0.5.0;

contract ConcreteOld {
    uint256 public myNumber;

    constructor(uint256 initialNumber) public {
        myNumber = initialNumber;
    }

    function setNumber(uint256 newNumber) public {
        myNumber = newNumber;
    }
}
