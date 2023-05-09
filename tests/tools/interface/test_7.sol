pragma solidity ^0.8.19;

interface IMock {
    error Error1();
    error Error2();
    error Error3();
    enum Status { Active, Pending, Canceled }
    struct Foo {
        uint256 bar;
        address baz;
    }
    function foo() external returns (Foo memory);
    function status() external returns (Status);
    function function1() external pure returns (address);
}

