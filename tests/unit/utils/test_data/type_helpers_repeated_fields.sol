// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

type Amount is uint256;

enum Flag {
    A,
    B
}

interface IThing {}

// Each struct holds the same convertible type twice. The second occurrence must be
// converted just like the first one -- it is a sibling, not a recursive back-edge.
struct WithAlias {
    Amount a;
    Amount b;
}

struct WithEnum {
    Flag a;
    Flag b;
}

struct WithContract {
    IThing a;
    IThing b;
}

contract B {
    function fAlias(WithAlias calldata p) external {}

    function fEnum(WithEnum calldata p) external {}

    function fContract(WithContract calldata p) external {}
}
