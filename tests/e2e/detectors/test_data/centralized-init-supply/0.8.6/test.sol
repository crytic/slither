// SPDX-License-Identifier: MIT
pragma solidity >=0.6.0 <0.9.0;

contract TestContract {
    struct BalancesStruct {
        address owner;
        uint256[] balances;
    }
    address owner;
    mapping(address => uint256) public balances;
    mapping (address => BalancesStruct) public stackBalance;
    constructor() {
        mint();
        balances[owner]+=1;
        stackBalance[msg.sender].owner = msg.sender;
    }
    function getStateVar() public view returns (uint256) {
        return stackBalance[msg.sender].balances.length;
    }
    function mint() public {
        balances[msg.sender]+=1;
    }
}
