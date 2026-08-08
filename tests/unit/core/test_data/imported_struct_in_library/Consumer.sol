// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import {Structs} from "./Structs.sol";

contract Consumer {
    Structs.ShiftChanges public currentChanges;
    Structs.Nested public nestedData;

    function updateShift(uint256 oldShift, uint256 newShift) external {
        currentChanges = Structs.ShiftChanges(oldShift, newShift);
    }

    function getChanges() external view returns (uint256, uint256) {
        return (currentChanges.oldShift, currentChanges.newShift);
    }
}
