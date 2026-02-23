// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// --- Should be flagged ---

contract UnusedEventContract {
    event NeverEmitted(address indexed user);
    event AlsoNeverEmitted(uint256 value, string reason);

    event ActuallyEmitted(uint256 value);

    function action() external {
        emit ActuallyEmitted(100);
    }
}

// --- Should NOT be flagged ---

contract EmitsAll {
    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    function transfer(address to, uint256 amount) external {
        emit Transfer(msg.sender, to, amount);
    }

    function approve(address spender, uint256 amount) external {
        emit Approval(msg.sender, spender, amount);
    }
}

// --- Inheritance tests ---

contract Base {
    event BaseEvent(uint256 value);
}

contract Child is Base {
    function emitIt() external {
        emit BaseEvent(42);
    }
}

// Unused event in base, never emitted anywhere
contract BaseUnused {
    event OrphanEvent(address who);
}

contract ChildNoEmit is BaseUnused {
    function doNothing() external pure {}
}

// --- Interface should not be flagged ---

interface IExample {
    event InterfaceEvent(uint256 id);
}

contract Implementor is IExample {
    // InterfaceEvent is inherited from interface, not declared here
    function trigger() external {
        emit InterfaceEvent(1);
    }
}
