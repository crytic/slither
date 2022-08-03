// pragma solidity ^0.4.24;

abstract contract Token{
    function transfer(address to, uint value) external virtual;
    function approve(address spender, uint value) external virtual;
    function transferFrom(address from, address to, uint value) external virtual;
    function totalSupply() external virtual;
    function balanceOf(address who) external virtual;
    function allowance(address owner, address spender) external virtual;
}
