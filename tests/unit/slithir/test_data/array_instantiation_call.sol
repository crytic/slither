// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

struct B{
    uint256 x;
}

contract A {
    function f(uint256[2] calldata arr) external {}
    function f(B[2] calldata arr) external {}
    function f(uint256[4] calldata arr) external {}
}

contract C {
    // TEST CASE 1: Simple array literal of primitives.
    // This case was also bugged by the array instantiation issue.
    function test_primitive_array_instantiation(A a, uint256 num) public {
        a.f([0, num]);
    }

    // TEST CASE 2: Complex array literal of structs with arithmetic.
    // This is the original complex bug case.
    function test_struct_array_instantiation(A a, uint256 num) public {
        a.f([B(num), B(num + 1 )]); 
    }


}
