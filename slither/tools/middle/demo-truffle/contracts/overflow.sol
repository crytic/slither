contract Overflow {
    function z(uint32 x, uint32 y) public returns (uint32) {
        uint32 ret = 0;
        if (x < 1000 && y < 1000) {
            will_it_overflow(x, y);
        }
        return ret;
    }

    function will_it_overflow(uint32 x, uint32 y) public returns (uint32) {
        return x * y;
    }
}
