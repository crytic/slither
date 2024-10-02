contract C {
    uint private a;

    function ifWithoutElse() public {
        if (a > 100) {
            a = 100;
        }
    }

    function ifWithElse() public {
        if (a < 50) {
            a = 50;
        } else {
            a /= 2;
        }
    }

    function ifWithElseIf() public {
        if (a % 2 == 0) {
            a += 1;
        } else if (a % 3 == 0) {
            a /= 3;
        } else if (a % 4 == 0) {
            a *= 2;
        }
    }

    function ifWithElseIfElse() public {
        if (a >= 100) {
            a = 100;
        } else if (a < 50) {
            a = 80;
        } else {
            a = 75;
        }
    }
}