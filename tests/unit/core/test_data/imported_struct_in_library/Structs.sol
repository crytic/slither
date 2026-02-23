// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library Structs {
    struct ShiftChanges {
        uint256 oldShift;
        uint256 newShift;
    }

    struct Nested {
        ShiftChanges changes;
        address updater;
    }
}
