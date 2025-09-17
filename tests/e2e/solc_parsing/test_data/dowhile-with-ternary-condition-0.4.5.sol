contract C {
    function f() public {
        bool a = true;
        bool b = true;
        bool c = true;
        int x = 4;
        int y = 4;
        do {
            x++;
            y--;
        } while (a ? b : c);

        do {
            x--;
            y++;
        } while (5 == (a ? x : y));
    }
}
