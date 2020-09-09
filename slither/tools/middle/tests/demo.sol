contract Contract {
    function sanitize_input(uint x, uint y) public {
        if (x < 1000 && y < 1000) {
            passthrough(x, y);
        }
    }

    function passthrough(uint x, uint y) public {
        will_it_overflow(x, y);
    }

    function will_it_overflow(uint x, uint y) public {
        uint w = x + y;
    }
}
