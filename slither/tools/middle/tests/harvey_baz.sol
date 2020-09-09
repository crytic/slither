contract Baz {

    bool private state1;
    bool private state2;
    bool private state3;
    bool private state4;
    bool private state5;

    function baz(int256 a, int256 b, int256 c) public returns (int256) {
        int256 ret;
        int256 d = b + c;
        if (d < 1) {
            if (b < 3) {
                state1 = true;
                ret = 1;
            }
            if (a == 42) {
                state2 = true;
                ret = 2;
            }

            state3 = true;
            ret = 3;
        }
        return ret;
    }
}