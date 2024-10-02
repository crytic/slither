pragma solidity ^0.8.4;
interface I {
  enum SomeEnum { ONE, TWO, THREE }
  error ErrorWithEnum(SomeEnum e);
}

struct St{
    uint v;
}

uint256 constant MAX = 5;

error ErrorSimple();
error ErrorWithArgs(uint, uint);
error ErrorWithStruct(St s);
error ErrorWithConst(uint256[MAX]);


contract VendingMachine is I {

    uint256 constant CMAX = 10;
    error CErrorWithConst(uint256[CMAX]);

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
    function err5(uint256[MAX] calldata a) public {
        revert ErrorWithConst(a);
    }
    function err6(uint256[CMAX] calldata a) public {
        revert CErrorWithConst(a);
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

contract ContractArgCustomError {
    error E(ContractArgCustomError a);

    function f() payable external {
      g();
    }
    
    function g() private {
      bool something = h();
      if (something) {
        revert E(this);
      }
    }

    function h() private returns (bool something) {
    }
}

