
// a simple contract
contract A {

}

// inheritance, no constructor
contract B is A {
    constructor(uint a) public {

    }
}

// inheritance, init in inheritance
contract C is B(4) {

}

// inheritance, init in constructor
contract D is B {
    constructor() B(2) public {

    }
}

// abstract contract
abstract contract E is B {
}

// diamond inheritance
contract F is A {}
contract G is A {}
contract H is F, G {

}