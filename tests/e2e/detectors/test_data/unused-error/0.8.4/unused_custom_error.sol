// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.4;

// Top-level error - unused
error TopLevelUnused();

// Top-level error - used
error TopLevelUsed(address account);

contract UnusedErrorTest {
    // Contract-level error - unused
    error Unauthorized();

    // Contract-level error - used
    error InsufficientBalance(uint256 available, uint256 required);

    // Contract-level error - unused with parameters
    error InvalidAmount(uint256 amount);

    address payable owner = payable(msg.sender);
    uint256 public balance;

    function withdraw(uint256 amount) public {
        if (msg.sender != owner) {
            // Using InsufficientBalance but not Unauthorized
            revert InsufficientBalance(balance, amount);
        }
        owner.transfer(amount);
    }

    function topLevelCheck(address account) public pure {
        // Using top-level error
        revert TopLevelUsed(account);
    }
}

// Contract that uses all its errors (no findings expected)
contract NoUnusedErrors {
    error AccessDenied();
    error InvalidInput(string reason);

    function checkAccess(bool allowed) public pure {
        if (!allowed) {
            revert AccessDenied();
        }
    }

    function validateInput(string memory input) public pure {
        if (bytes(input).length == 0) {
            revert InvalidInput("empty input");
        }
    }
}

// Interface - should not report (signature only)
interface IErrors {
    error InterfaceError();
}
