// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Minimal ERC-20 implementation
contract MyERC20 {
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    function totalSupply() external view returns (uint256) { return 0; }
    function balanceOf(address) external view returns (uint256) { return 0; }
    function transfer(address, uint256) external returns (bool) { return true; }
    function allowance(address, address) external view returns (uint256) { return 0; }
    function approve(address, uint256) external returns (bool) { return true; }
    function transferFrom(address, address, uint256) external returns (bool) { return true; }

    // Optional
    function name() external view returns (string memory) { return "Token"; }
    function symbol() external view returns (string memory) { return "TKN"; }
    function decimals() external view returns (uint8) { return 18; }
}

// Partial ERC-20 (missing some functions)
contract PartialERC20 {
    function totalSupply() external view returns (uint256) { return 0; }
    function balanceOf(address) external view returns (uint256) { return 0; }
    function transfer(address, uint256) external returns (bool) { return true; }
    // Missing: allowance, approve, transferFrom
}

// Non-token contract
contract NotAToken {
    uint256 public value;

    function setValue(uint256 _value) external {
        value = _value;
    }
}
