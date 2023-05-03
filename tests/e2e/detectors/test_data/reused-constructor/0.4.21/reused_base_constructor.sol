contract A{
    uint num = 5;
    function A(uint x) public{
        num += x;
    }
}

contract B is A{
    function B(uint y) A(y * 3) public{
        uint i = 1;
    }
}

contract C is B{
    function C(uint y) A(y * 2) public{
        uint i = 1;
    }
}

contract D is B(1), C(1) {
    function D() B(3) C(2) public {
        uint i = 1;
    }
}

contract E is B(1), C, D() {
    function E() B(1) C(2) D() public {
        uint i = 1;
    }
}


contract F is B {
    function F() A(1) public {
        uint i = 1;
    }
}