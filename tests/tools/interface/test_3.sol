pragma solidity ^0.8.19;

interface IMock {
    event Event1();
    event Event2(address);
    event Event3(uint256, uint72);
    error Error1();
    error Error2();
    error Error3();
    enum Status { Active, Pending, Canceled }
    struct Foo {
        uint256 bar;
        address baz;
    }
    function foo() external returns (uint256, address);
    function status() external returns (uint8);
    function function1() external pure returns (address);
}

