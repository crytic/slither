//pragma solidity ^0.4.24;

library SafeMath{
    function add(uint a, uint b) public returns(uint){
        return a+b;
    }
}

abstract contract Target{
    function f() public virtual returns(uint);
    function g() public virtual returns(uint, uint);
}

contract User{

    using SafeMath for uint;

    function test(Target t) public{
        t.f();
    
        // example with library usage
        uint a;
        a.add(0);

        // The value is not used
        // But the detector should not detect it
        // As the value returned by the call is stored
        // (unused local variable should be another issue) 
        uint b = a.add(1);

        t.g();

        (uint c, uint d) = t.g();

        // Detected as unused return
        (uint e,) = t.g();
    }
}
