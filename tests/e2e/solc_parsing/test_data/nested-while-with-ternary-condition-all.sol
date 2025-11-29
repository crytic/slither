contract C {
    function f() public {
        bool a = true;
        bool b = true;
        bool c = true;
        int x = 4;
        int y = 4;
        while (a ? b : c) {
            while (5 == (a ? x : y)) {
                y++;
            }
            x--;
        }
    }
}
