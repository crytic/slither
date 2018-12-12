contract BaseContract{
    
    function f1() public{

    }
}

contract Contract is BaseContract{

    uint a;

    function entry_point() public{
        f1();
        f2();
    }

    function f1() public{
        super.f1();
    }

    function f2() public{

    }
    
    // not reached from entry_point
    function f3() public{

    }
}
