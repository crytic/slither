contract Test {
    /* Solidity `^` with a decimal constant is still reported */
    function bad(uint a) internal pure returns (uint) {
        return a ^ 2;
    }

    /* Yul has no exponentiation operator, `xor` in assembly is a bitwise xor */
    function goodAssembly(uint a) internal pure returns (uint r) {
        assembly {
            r := xor(a, 2)
        }
    }

    function goodAssemblyThenSolidity(uint a) internal pure returns (uint r) {
        assembly {
            r := xor(a, 32)
        }
        /* The assembly block ended, so this one is reported again */
        r = r ^ 10;
    }
}
