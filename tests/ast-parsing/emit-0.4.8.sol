contract C {
    event E(uint);

    function emitNoKeyword() public {
        E(1);
        C.E(1);
    }

    function cursed() public {
        var x = E;
        x(1);
        x(2);
    }
}