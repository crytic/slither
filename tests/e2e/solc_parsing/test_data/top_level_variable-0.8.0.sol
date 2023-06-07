uint constant A = 10;

struct St{
    uint[A] b;
}

function f() returns(uint){
    return A;
}

contract T{
    function g() public{
        f();
    }

}

