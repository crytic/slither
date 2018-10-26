pragma solidity ^0.4.24;

contract naming {

    enum Numbers {ONE, TWO}
    enum numbers {ONE, TWO}

    uint constant MY_CONSTANT = 1;
    uint constant MY_other_CONSTANT = 2;

    uint Var_One = 1;
    uint varTwo = 2;

    struct test {

    }

    struct Test {

    }

    event Event_(uint);
    event event_(uint);

    function getOne() constant returns (uint)
    {
        return 1;
    }

    function GetOne() constant returns (uint)
    {
        return 1;
    }

    function setInt(uint number1, uint Number2)
    {

    }


    modifier CantDo() {
        _;
    }

    modifier canDo() {
        _;
    }
}

contract Test {

}

contract T {
    uint private _myPrivateVar;
    uint _myPublicVar;


    function test(uint _unused, uint _used) returns(uint){
        return _used;}


    uint k = 1;

    uint constant M = 1;

    uint l = 1;
}
