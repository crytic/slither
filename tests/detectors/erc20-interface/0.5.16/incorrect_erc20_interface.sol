// pragma solidity ^0.4.24;

contract Token{
    function transfer(address to, uint value) external;
    function approve(address spender, uint value) external;
    function transferFrom(address from, address to, uint value) external;
    function totalSupply() external;
    function balanceOf(address who) external;
    function allowance(address owner, address spender) external;
}
