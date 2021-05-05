contract C {
    function f() public {
        false ? 1 : 2;
        5 == 6 ? 1 : 2;
        1 + 2 == 3 ? 4 + 5 == 6 ? int8(0) : -1 : -2;
        true ? "a" : "b";
        false ? (1, 2) : (3, 4);
    }
}