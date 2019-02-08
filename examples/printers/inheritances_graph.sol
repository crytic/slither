contract A {
    function f() public pure returns (uint) {
        return 0;
    }

    function g() public pure returns (uint) {
        return 0;
    }
}

contract B {
    function g() public pure returns (uint) {
        return 0;
    }
}

contract C is A, B {
    function f() public pure returns (uint) {
        return 0;
    }
}