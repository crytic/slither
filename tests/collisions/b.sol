struct St{
    uint b;
}

contract A{
    function h() public {}
}

contract B1{
    A a;
    St s;
    function g() internal returns(uint){
        a.h();
        return s.b;
    }
}


