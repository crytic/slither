contract C {
    function f(uint z) public {
        uint y;
        y = x + 9 + z; // x is being used before declaration
        uint x = 7;

        for (uint j = 0; j < z; j++) {
            for (uint i = 10; i > 0; i--) {
                x += i;
            }
        }

        // On lines below, 'i' could be used pre-declaration if the outer loop above did not enter to declare it.
        for (i = 10; i > 0; i--) {
            x += i;
        }
    }
}