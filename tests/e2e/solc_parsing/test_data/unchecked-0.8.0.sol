contract C {
    function f(uint a, uint b) pure public returns (uint) {
        // This addition will wrap on underflow.
        unchecked { return a - b; }
    }
    function g(uint a, uint b) pure public returns (uint) {
        // This addition will revert on underflow.
        return a - b;
    }
}
