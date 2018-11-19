pragma solidity ^0.4.24;

library SafeMath{
    function add(uint a, uint b) public returns(uint){
        return a+b;
    }
}

contract Target{
    function f() returns(uint);
}

contract User{

    using SafeMath for uint;

    function test(Target t){
        t.f();
    
        // example with library usage
        uint a;
        a.add(0);

        // The value is not used
        // But the detector should not detect it
        // As the value returned by the call is stored
        // (unused local variable should be another issue) 
        uint b = a.add(1);
    }
}
