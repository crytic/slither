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
    function g(A a, uint256 num) public {
        a.f([0, num]);
    }

    function e(A a, uint256[2] calldata numArr) public {
        a.f(numArr);
    }

    function e(A a, uint256 num) public {
        a.f([B(num), B(num + 1 )]); 
    }

}