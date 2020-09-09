contract Test {
    function f(uint n) public returns(uint res) {
        uint counter = 0;
        for (uint i = 0; i < n; i++) {
            counter += 1;
        }
        return counter;
    }
}