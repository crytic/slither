pragma solidity ^0.8.4;

contract Test {
    address owner;

    error NotOwner();

    modifier onlyOwnerStr() {
        if (msg.sender == owner) {
            _;
        } else {
            revert("not owner");
        }
    }

    modifier onlyOwnerErr() {
        if (msg.sender == owner) {
            _;
        } else {
            revert NotOwner();
        }
    }

    function f() external onlyOwnerStr returns (uint256) {
        return 1;
    }

    function g() external onlyOwnerErr returns (uint256) {
        return 2;
    }
}
