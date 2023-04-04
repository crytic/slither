contract C {
    function f() public {
        uint assign;
        assign = 10;

        assign |= 10;
        assign ^= 10;
        assign &= 10;
        assign <<= 10;
        assign >>= 10;
        assign += 10;
        assign -= 10;
        assign *= 10;
        assign /= 10;
        assign %= 10;
    }
}