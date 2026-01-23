// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// Test library for library call traversal
library TestLib {
    uint256 constant LIB_CONST = 100;

    function libFunc(uint256 x) internal pure returns (uint256) {
        return x + LIB_CONST;
    }
}

// Test contract with various call graph patterns
contract TestCallGraph {
    // State variables for tracking traversal
    uint256 public stateA;
    uint256 public stateB;
    uint256 public stateC;
    uint256 public stateTop;
    uint256 public stateLeft;
    uint256 public stateRight;
    uint256 public stateBottom;
    uint256 public stateModifier;
    uint256 public stateLib;
    uint256 public stateStandalone;

    // Modifier that reads/writes state
    modifier testModifier() {
        stateModifier = 1;
        _;
    }

    // Simple chain: chainA -> chainB -> chainC
    function chainA() public {
        stateA = 1;
        chainB();
    }

    function chainB() internal {
        stateB = 2;
        chainC();
    }

    function chainC() internal {
        stateC = 3;
    }

    // Cycle: cycleA -> cycleB -> cycleA (via external call simulation)
    // Note: Internal calls can't create true cycles, but we test the pattern
    function cycleA() public {
        stateA = 10;
        cycleB();
    }

    function cycleB() internal {
        stateB = 20;
        // In real code, this would be an external call to create a cycle
        // For testing, we just ensure both functions are traversed
    }

    // Diamond pattern: diamondTop -> diamondLeft & diamondRight -> diamondBottom
    function diamondTop() public {
        stateTop = 1;
        diamondLeft();
        diamondRight();
    }

    function diamondLeft() internal {
        stateLeft = 2;
        diamondBottom();
    }

    function diamondRight() internal {
        stateRight = 3;
        diamondBottom();
    }

    function diamondBottom() internal {
        stateBottom = 4;
    }

    // Function with modifier
    function withModifier() public testModifier {
        stateA = 100;
    }

    // Function with library call
    function withLibraryCall(uint256 x) public {
        stateLib = TestLib.libFunc(x);
    }

    // Standalone function with no calls
    function standalone() public {
        stateStandalone = 999;
    }
}
