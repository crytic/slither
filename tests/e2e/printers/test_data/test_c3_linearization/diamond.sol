// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Diamond inheritance pattern for C3 linearization test
// Expected linearization for D: [D, C, B, A]

contract A {
    uint256 public valueA;

    constructor() {
        valueA = 1;
    }

    function foo() public virtual returns (string memory) {
        return "A";
    }
}

contract B is A {
    uint256 public valueB;

    constructor() {
        valueB = 2;
    }

    function foo() public virtual override returns (string memory) {
        return "B";
    }
}

contract C is A {
    uint256 public valueC;

    constructor() {
        valueC = 3;
    }

    function foo() public virtual override returns (string memory) {
        return "C";
    }
}

contract D is B, C {
    uint256 public valueD;

    constructor() {
        valueD = 4;
    }

    function foo() public override(B, C) returns (string memory) {
        return "D";
    }
}
