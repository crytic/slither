contract C {
    function f() public {
        var implicitUint8 = 0;
        uint8 explicitUint8 = 0;
        var implicitUint16 = 256;
        uint16 explicitUint16 = 256;

        var implicitType = uint[];

        uint[][][] memory uintArr;

        address ternaryInit = msg.sender.balance > 0 ? msg.sender : block.coinbase;

        uint overwritten;
        uint overwritten1 = overwritten = 10;
    }
}