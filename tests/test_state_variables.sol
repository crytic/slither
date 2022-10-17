pragma solidity ^0.8.4;

contract BaseContract{
    uint256 public one;
    uint256[50] private __gap;
    uint256 internal two;
}

contract DerivedContract is BaseContract{
    uint256 public three;
    uint256[50] private __gap;
    uint256 internal four;
}