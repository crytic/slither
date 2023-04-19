pragma solidity ^0.8.0;

contract Concrete {
    uint256 public value;

    function setValue(uint256 newValue) public {
        value = newValue;
    }
}
