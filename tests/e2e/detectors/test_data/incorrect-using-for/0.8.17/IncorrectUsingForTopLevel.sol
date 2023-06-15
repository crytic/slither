pragma solidity 0.8.17;

struct S1
{
    uint __;
}

struct S2
{
    uint128 __;
}

enum E1
{
    A,
    B
}

enum E2
{
    A,
    B
}

contract C0
{

}

contract C1 is C0
{

}

contract C2 is C1
{

}

contract C3
{

}

type custom_uint is uint248;
type custom_int is int248;

library L
{
    function f0(C0) public pure {}
    function f1(bool) public pure {}
    function f2(string memory) public pure {}
    function f3(bytes memory) public pure {}
    function f4(uint248) public pure {}
    function f5(int248) public pure {}
    function f6(address) public pure {}
    function f7(bytes17) public pure {}
    function f8(S1 memory) public pure {}
    function f9(E1) public pure {}
    function f10(mapping(int => uint) storage) public pure {}
    function f11(string[] memory) public pure {}
    function f12(bytes[][][] memory) public pure {}
    function f13(custom_uint) public pure {}
}

// the following statements are correct
using L for C2;
using L for bool;
using L for string;
using L for bytes;
using L for uint240;
using L for int16;
using L for address;
using L for bytes16;
using L for S1;
using L for E1;
using L for mapping(int => uint);
using L for string[];
using L for bytes[][][];
using L for custom_uint;

// the following statements are incorrect
using L for C3;
using L for bytes17[];
using L for uint;
using L for int;
using L for bytes18;
using L for S2;
using L for E2;
using L for mapping(int => uint128);
using L for mapping(int128 => uint);
using L for string[][];
using L for bytes[][];
using L for custom_int;
