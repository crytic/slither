contract C {
    function f() internal returns (uint256 a) {
        assembly {
            a := and(1, shr(a, 8))
        }
    }
}
