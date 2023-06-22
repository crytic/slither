pragma solidity ^0.8.19;

type Int is int;
using {add as +, eq as ==, add, neg as -, Lib.f} for Int global;

function add(Int a, Int b) pure returns (Int) {
    return Int.wrap(Int.unwrap(a) + Int.unwrap(b));
}

function eq(Int a, Int b) pure returns (bool) {
    return true;
}

function neg(Int a) pure returns (Int) {
    return a;
}

library Lib {
    function f(Int r) internal {}
}

contract T {
    function add_function_call(Int b, Int c) public returns(Int) {
        Int res = add(b,c);
        return res;
    }

    function add_op(Int b, Int c) public returns(Int) {
        return b + c;
    }

    function lib_call(Int b) public {
        return b.f();
    }

    function neg_usertype(Int b) public returns(Int) {
        Int res = -b;
        return res;
    }

    function neg_int(int b) public returns(int) {
        return -b;
    }

    function eq_op(Int b, Int c) public returns(bool) {
        return b == c;
    }
}
