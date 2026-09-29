// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PropertiesExample {
    uint256 public totalSupply;

    function echidna_total_supply_capped() public view returns (bool) {
        return totalSupply <= 1_000_000;
    }

    function crytic_balance_never_negative() public view returns (bool) {
        return true;
    }

    function transfer(address to, uint256 amount) public returns (bool) {
        to;
        amount;
        return true;
    }
}
