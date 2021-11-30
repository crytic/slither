pragma solidity ^0.8.4;

struct St{
    uint v;
}

error ErrorSimple();
error ErrorWithArgs(uint, uint);
error ErrorWithStruct(St s);

contract VendingMachine {

    function err0() public {
        revert ErrorSimple();
    }
    function err1() public {
        St memory s;
        revert ErrorWithStruct(s);
    }
    function err2() public{
        revert ErrorWithArgs(10+10, 10);
    }
    function err3() public{
        revert('test');
    }
}

contract A{

    error MyError(uint);
    function f() public{
        revert MyError(2);
    }
}

contract B is A{
    function g() public{
        revert MyError(2);
    }
}

