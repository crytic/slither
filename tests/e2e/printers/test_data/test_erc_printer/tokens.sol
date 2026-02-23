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

// Minimal ERC-721 implementation
contract MyERC721 {
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    function balanceOf(address) external view returns (uint256) { return 0; }
    function ownerOf(uint256) external view returns (address) { return address(0); }
    function safeTransferFrom(address, address, uint256, bytes calldata) external {}
    function safeTransferFrom(address, address, uint256) external {}
    function transferFrom(address, address, uint256) external {}
    function approve(address, uint256) external {}
    function setApprovalForAll(address, bool) external {}
    function getApproved(uint256) external view returns (address) { return address(0); }
    function isApprovedForAll(address, address) external view returns (bool) { return false; }
    // ERC-165 required for ERC-721
    function supportsInterface(bytes4) external view returns (bool) { return true; }

    // Optional metadata
    function name() external view returns (string memory) { return "NFT"; }
    function symbol() external view returns (string memory) { return "NFT"; }
    function tokenURI(uint256) external view returns (string memory) { return ""; }
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

// Interface should be excluded
interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}
