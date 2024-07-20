contract C {
    function f() public {
        bool a = true;
        bool b = true;
        bool c = true;
        int x = 4;
        int y = 4;
        for (int i = 0; a ? b : c; i++) {
            x++;
            y--;
        }

        for (int j = 0; a ? b : c; j++) a = false;

        for (int k = 0; 5 == ((k < 3) ? x : y); k--) {
            x--;
            y++;
        }
    }
}
