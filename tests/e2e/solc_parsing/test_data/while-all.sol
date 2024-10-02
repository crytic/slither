contract C {
    function f() public {
        bool go = true;
        while (go) {
            go = false;
        }

        go = true;
        while (go) go = false;
    }
}