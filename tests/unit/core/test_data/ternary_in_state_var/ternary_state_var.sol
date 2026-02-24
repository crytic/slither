// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract A {
    struct S {
        uint32 user;
    }
}

// Ternary expression in state variable initializer with struct member access.
// Before the fix, this caused:
//   SlithIRError: Ternary operator are not convertible to SlithIR
// because constructor variable nodes were not processed by ternary rewriting.
contract B {
    A.S a;
    A.S b;
    uint32 result = (true ? a.user : b.user);
}
