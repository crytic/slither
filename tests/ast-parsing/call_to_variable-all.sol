contract C{
    uint public v;
}

contract D{
    function f(C c) public{
        c.v();
    }
}
