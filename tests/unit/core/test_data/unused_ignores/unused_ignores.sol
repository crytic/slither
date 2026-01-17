// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

// Test contract for unused slither-disable comments

// This is an unused next-line ignore - the naming_convention detector is not triggered
// slither-disable-next-line naming-convention
contract UnusedIgnores {
    // Naming convention would be triggered here, so this USED
    // slither-disable-next-line naming-convention
    uint public Bad_variable_name;

    // This is UNUSED - no detector is triggered for this line
    // slither-disable-next-line reentrancy-eth
    uint public normal_var;

    // slither-disable-start naming-convention
    // This block has naming issues, so it's USED
    uint public Another_Bad_Name;
    uint public Yet_Another;
    // slither-disable-end naming-convention

    // slither-disable-start reentrancy-eth
    // This block has no reentrancy, so it's UNUSED
    function simpleFunction() public pure returns (uint) {
        return 42;
    }
    // slither-disable-end reentrancy-eth

    // Multiple detectors on one line - some used, some not
    // slither-disable-next-line naming-convention,reentrancy-eth
    uint public Mixed_Case_No_Reentrancy;
}
