// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test inheritance patterns for derived_contracts property
//
// Inheritance graph:
//
//       Base
//      /    \
//   Child1  Child2
//      \    /
//     Grandchild
//
// Additionally:
//   Standalone (no inheritance)
//   Deep chain: L1 <- L2 <- L3 <- L4

contract Base {
    uint public baseValue;
}

contract Child1 is Base {
    uint public child1Value;
}

contract Child2 is Base {
    uint public child2Value;
}

contract Grandchild is Child1, Child2 {
    uint public grandchildValue;
}

contract Standalone {
    uint public standaloneValue;
}

// Deep inheritance chain
contract L1 {
    uint public l1Value;
}

contract L2 is L1 {
    uint public l2Value;
}

contract L3 is L2 {
    uint public l3Value;
}

contract L4 is L3 {
    uint public l4Value;
}
