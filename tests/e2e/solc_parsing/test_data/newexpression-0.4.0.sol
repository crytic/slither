contract B {
    function B() public {}
}

contract C {
    function f() public {
        new B;

        new uint[];
        new uint[][];
    }
}