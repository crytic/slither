contract Test{
    function unused() internal{
        uint i = 1;
    }
}


contract Test2{

    function unused_but_shadowed() internal virtual{
        uint i = 1;
    }
}

contract Test3 is Test2{
    function unused_but_shadowed() internal override{
        uint i = 1;
    }

    function f() public{
        unused_but_shadowed();
    }
}

contract Test4 is Test2{
    function unused_but_shadowed() internal override{
        uint i = 1;
    }
}

abstract contract Test5 {
    function unused_but_abstract() internal virtual;
}
