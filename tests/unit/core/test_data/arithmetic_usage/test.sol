function protected(uint a, uint b) returns(uint){
    return (a + b) * (a + b);
}

function not_protected_asm(uint a, uint b) returns(uint){
    uint c;
    assembly{
        c := mul(add(a,b), add(a,b))
    }
    return c;
}

function not_protected_unchecked(uint a, uint b) returns(uint){
    uint c;
    unchecked{
        return (a + b) * (a + b);
    }

}

contract A{

    function f(uint a, uint b) public{
        protected(a,b);
        not_protected_asm(a, b);
        not_protected_unchecked(a, b);
    }

}