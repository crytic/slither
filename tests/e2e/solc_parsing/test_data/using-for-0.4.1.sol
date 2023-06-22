library L1 {
    function f(uint a) public returns (uint) {
        return a;
    }
}

library L2 {
    function f(bytes32 a) public returns (bytes32) {
        return a;
    }
}

contract C {
    using L1 for uint;
    using L2 for *;
}