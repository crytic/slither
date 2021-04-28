contract A{
    uint num = 5;
    constructor(uint x) public{
        num += x;
    }
}

contract B is A{
    constructor(uint y) A(y * 3) public{

    }
}

contract C is B{
    constructor(uint y) A(y * 2) public{

    }
}

contract D is B(1), C(1) {
    constructor() B(3) C(2) public {

    }
}

contract E is B(1), C, D() {
    constructor() B(1) C(2) D() public {

    }
}


contract F is B {
    constructor() A(1) public {

    }
}