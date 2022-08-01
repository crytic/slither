struct St{
    uint a;
}

contract A{
    function f() public {}
}

contract B0{
    A a;
    St s;
    function g() internal returns(uint){
        a.f();
        return s.a;
    }
}


