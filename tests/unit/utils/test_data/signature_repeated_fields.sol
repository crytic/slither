// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Regression for solidity_signature converting only the first sibling field
// whose type needs conversion (issue #3064).

type Amount is uint256;

enum Flag {
    A,
    B
}

interface IThing {
    function x() external;
}

struct Pair {
    Amount a;
    Amount b; // same user-defined value type as `a`
}

struct EnumPair {
    Flag a;
    Flag b; // same enum type
}

struct ContractPair {
    IThing a;
    IThing b; // same interface type
}

struct Inner {
    uint256 x;
    address y;
}

struct Outer {
    Inner first;
    Inner second; // same non-recursive structure type as `first`
}

contract RepeatedFields {
    function fAlias(Pair calldata p) external pure returns (uint256) {
        return Amount.unwrap(p.a) + Amount.unwrap(p.b);
    }

    function fEnum(EnumPair calldata p) external pure returns (uint8) {
        return uint8(p.a);
    }

    function fContract(ContractPair calldata p) external pure returns (address) {
        return address(p.a);
    }

    function fRepeatedStruct(Outer calldata o) external pure returns (uint256) {
        return o.first.x;
    }
}
