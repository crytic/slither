contract B {
    constructor() public {}
}

contract C {
    function f() public {
        new B;

        new uint[];
        new uint[][];
//        (new uint[]){value: 10}(2);
    }
}