contract C {
    function f() public {
        bool a = true;
        bool b = true;
        bool c = true;
        int x = 4;
        int y = 4;
        if (a ? b : c) {
            x++;
            y--;
        }

        if (a ? b : c) a = false;

        if (5 == (a ? x : y)) {
            x--;
            y++;
        }
    }
}
