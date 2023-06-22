
// a simple contract
contract A {

}

// inheritance, no constructor
contract B is A {
    function B(uint a) {

    }
}

// inheritance, init in inheritance
contract C is B(4) {

}

// inheritance, init in constructor
contract D is B {
    function D() B(2) {

    }
}

// abstract contract
contract E is B {
}

// diamond inheritance
contract F is A {}
contract G is A {}
contract H is F, G {

}