contract C {
    function f(uint a) public returns (uint x) {
        x = a;
        if(a == 1) {
            return a;
        } else {
            for (uint i = 0; i < 10; i++) {
                if (x > 10) {
                    if (a < 0) {
                        x = 10 * x;
                    } else {
                        throw;
                    }
                } else {
                    x++;
                }
            }
        }
    }

    function g(uint a, uint b) public returns (uint x, uint y) {
        x = a;
        y = b;
        if(a == 1) {
            return (a, b);
        } else {
            for (uint i = 0; i < 10; i++) {
                if (x > 10) {
                    if (a < 0) {
                        x = 10 * x;
                        y = 10 * y;
                    } else {
                        throw;
                    }
                } else {
                    x++;
                    y--;
                }
            }
        }
    }

    struct St {
        uint value;
    }

    function h(St memory s) internal returns (St memory t) {
        t = St(1);
        if(s.value == 1) {
            return s;
        } else {
            t.value = 10;
        }
    }
}