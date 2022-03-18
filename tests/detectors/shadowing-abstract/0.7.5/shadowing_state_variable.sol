pragma solidity ^0.7.5;
contract BaseContract{
    uint256[50] private __gap;
}

contract DerivedContract is BaseContract{
    uint256[50] private __gap;
}
