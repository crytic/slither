//pragma solidity ^0.4.24;

contract A {
    error Unused1();
    error Unused2();
    error Unused3();

    function x() public pure {
        revert Unused1();
    }
}
