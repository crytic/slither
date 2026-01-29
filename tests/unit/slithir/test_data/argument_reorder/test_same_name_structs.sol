// Regression test for https://github.com/crytic/slither/issues/2217
// Two contracts define structs with the same name but different field counts.
// Slither must not crash when processing named struct constructor arguments.
contract A {
    struct S {
        int x;
    }

    function test() external pure returns (int) {
        S memory p = S({x: 1});
        return p.x;
    }
}

contract B {
    struct S {
        int x;
        int y;
    }

    function test() external pure returns (int) {
        S memory p = S({y: 4, x: 5});
        return p.x + p.y;
    }
}
