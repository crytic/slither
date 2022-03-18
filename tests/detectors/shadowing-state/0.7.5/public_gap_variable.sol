pragma solidity ^0.7.5;
contract BaseContract{
    uint256[50] private __gap;
    function f() external {}
}

contract DerivedContract is BaseContract{
    uint256[50] public __gap;
    function g() external {}
}
