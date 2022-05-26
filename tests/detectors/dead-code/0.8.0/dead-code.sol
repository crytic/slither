contract Test{
    function unused() internal{

    }
}


contract Test2{

    function unused_but_shadowed() internal virtual{

    }
}

contract Test3 is Test2{
    function unused_but_shadowed() internal override{

    }

    function f() public{
        unused_but_shadowed();
    }
}

contract Test4 is Test2{
    function unused_but_shadowed() internal override{

    }
}

abstract contract Test5 {
    function unused_but_abstract() internal virtual;
}
