//pragma solidity ^0.4.24;

contract A {
    error Unused1();
    error UsedError(address x);

    constructor() public {}

    function x() public view {
        uint256 d = 7;
        if (msg.sender == address(0)) {
            d = 100;
            revert UsedError(msg.sender);
        }
    }
}
