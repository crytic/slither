pragma solidity ^0.8.19;

interface IMock {
    event Event1();
    event Event2(address);
    event Event3(uint256, uint72);
    enum Status { Active, Pending, Canceled }
    struct Foo {
        uint256 bar;
        address baz;
    }
    function foo() external returns (Foo memory);
    function status() external returns (Status);
    function function1() external pure returns (address);
}

