contract C {
    function f() public {
        bool go = true;
        do {
            go = false;
        } while (go);

        go = true;
        do go = false;
        while (go);
    }
}