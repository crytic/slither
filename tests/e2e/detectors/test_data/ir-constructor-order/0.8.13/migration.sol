// SPDX-License-Identifier: MIT
pragma solidity >=0.8.13;

contract Base {
    uint internal threshold;
    uint internal unchanged = 9;
    constructor() { threshold = 42; }
    function readThreshold() internal view returns (uint) { return threshold; }
    function indirect() internal view returns (uint) { return readThreshold(); }
}

contract Direct is Base { uint public copied = threshold; }
contract Indirect is Base { uint public copied = indirect(); }
contract Immutable is Base { uint public immutable copied = threshold; }
contract Independent is Base { uint public copied = unchanged; }
contract Constant is Base { uint public copied = 42; }
contract SameContract {
    uint threshold;
    uint copied = threshold;
    constructor() { threshold = 42; }
}

contract Root { uint internal value; }
contract Left is Root { constructor() { value = 5; } }
contract Right is Root { uint internal copied = value; }
// Reversing the two bases reverses whether Left's constructor precedes Right's initializer.
contract RightAfterLeft is Left, Right {}
contract RightBeforeLeft is Right, Left {}
