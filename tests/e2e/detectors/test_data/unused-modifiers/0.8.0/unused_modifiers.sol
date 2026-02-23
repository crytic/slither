// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// --- Should be flagged ---

contract UnusedModifierContract {
    address public owner;

    modifier neverUsed() {
        require(msg.sender == owner);
        _;
    }

    modifier alsoNeverUsed() {
        require(msg.value > 0);
        _;
    }

    modifier actuallyUsed() {
        require(msg.sender != address(0));
        _;
    }

    function doSomething() external actuallyUsed {
        // uses actuallyUsed
    }
}

// --- Should NOT be flagged ---

contract AllModifiersUsed {
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    modifier nonZero(uint256 val) {
        require(val > 0);
        _;
    }

    function restricted() external onlyOwner {
        // uses onlyOwner
    }

    function validated(uint256 x) external nonZero(x) {
        // uses nonZero
    }
}

// --- Inheritance: virtual modifier overridden ---

contract BaseModifier {
    modifier baseMod() virtual {
        _;
    }
}

contract ChildModifier is BaseModifier {
    modifier baseMod() override {
        require(msg.sender != address(0));
        _;
    }

    function action() external baseMod {
        // uses overridden baseMod
    }
}

// --- Unused virtual modifier NOT overridden ---

contract UnusedVirtual {
    modifier unusedVirtualMod() virtual {
        _;
    }

    function nothing() external pure {}
}
