contract C {
    event E(uint);

    function emitWithKeyword() public {
        emit E(1);
        emit C.E(1);
    }
}