pragma solidity ^0.8.4;
interface I {
  enum SomeEnum { ONE, TWO, THREE }
  error ErrorWithEnum(SomeEnum e);
}

struct St{
    uint v;
}

error ErrorSimple();
error ErrorWithArgs(uint, uint);
error ErrorWithStruct(St s);


contract VendingMachine is I {

    function err0() public {
        revert ErrorSimple();
    }
    function err1() public {
        St memory s;
        revert ErrorWithStruct(s);
    }
    function err2() public{
        revert ErrorWithArgs(10+10, 10);
        revert ErrorWithArgs(uint(SomeEnum.ONE), uint(SomeEnum.ONE));
    }
    function err3() public{
        revert('test');
    }
    function err4() public {
        revert ErrorWithEnum(SomeEnum.ONE);
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

    function h() public returns(bytes4){
        return MyError.selector;
    }
}


