// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract A {
    uint256 public x;

    modifier m() virtual {
        x = 1;
        _;
    }

    modifier p(uint256 v) virtual {
        x = v;
        _;
    }
}

contract B is A {
    modifier m() virtual override {
        x = 2;
        _;
    }

    modifier p(uint256 v) virtual override {
        x = v + 1;
        _;
    }
}

contract C is B {
    modifier m() override {
        x = 3;
        _;
    }

    modifier p(uint256 v) override {
        x = v + 2;
        _;
    }

    function f() public A.m returns (uint256) {
        return x;
    }

    function g(uint256 v) public A.p(v) B.p(v) p(v) returns (uint256) {
        return x;
    }
}
