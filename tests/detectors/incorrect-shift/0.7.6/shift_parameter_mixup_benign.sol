contract C {
    function f() internal returns (uint256 a) {
        a << 2;
        4 >> a;

        assembly {
            a := shr(8, a)
        }
    }
}
