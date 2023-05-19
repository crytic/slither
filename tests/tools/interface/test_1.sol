pragma solidity ^0.4.18;

interface IWETH9 {
    event Approval(address, address, uint256);
    event Transfer(address, address, uint256);
    event Deposit(address, uint256);
    event Withdrawal(address, uint256);
    function name() external returns (string memory);
    function symbol() external returns (string memory);
    function decimals() external returns (uint8);
    function balanceOf(address) external returns (uint256);
    function allowance(address,address) external returns (uint256);
    function deposit() external payable;
    function withdraw(uint256) external;
    function totalSupply() external view returns (uint256);
    function approve(address,uint256) external returns (bool);
    function transfer(address,uint256) external returns (bool);
    function transferFrom(address,address,uint256) external returns (bool);
}

