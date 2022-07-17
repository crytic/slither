contract Test {   
    event Val(uint, uint);
    function f(uint a, uint b) public {
        emit Val(a, b);
    }
}
contract D {
    function bad() public {
        Test t = new Test();
        address(t).call(abi.encodeWithSelector(Test.f.selector,"test"));
    }
    function good() public {
        Test t = new Test();
        address(t).call(abi.encodeWithSelector(Test.f.selector, 1, 2));
    }
}

