contract C {
    event E(uint);

    function emitNoKeyword() public {
        E(1);
        C.E(1);
    }

    function emitWithKeyword() public {
        emit E(1);
        emit C.E(1);
    }

    function cursed() public {
        var x = E;
        x(1);
        x(2);

        emit x(1);
        emit x(2);
    }
}