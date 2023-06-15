pragma solidity ^0.8.19;

contract Mock {
    
    error Error1();
    error Error2();
    error Error3();

    event Event1();
    event Event2(address param);
    event Event3(uint256 num1, uint72 num2);
    
    struct Foo {
        uint256 bar;
        address baz;
    }

    enum Status {
        Active,
        Pending,
        Canceled
    }

    Foo public foo;

    Status public status;

    function function1() public pure returns (address){
        return address(0);
    }


}