// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BalanceRelianceTest {
    uint256 public savedBalance;
    uint256 public threshold;

    // BAD: Strict equality check with address.balance
    function checkExactBalance() public view returns (bool) {
        return address(this).balance == 1 ether;
    }

    // BAD: Strict inequality check with address.balance
    function checkNotBalance() public view returns (bool) {
        return address(this).balance != 0;
    }

    // BAD: Indirect strict equality (via local variable)
    function indirectCheck(uint256 expected) public view returns (bool) {
        uint256 currentBal = address(this).balance;
        return currentBal == expected;
    }

    // BAD: Saving balance to state variable
    function saveCurrentBalance() public {
        savedBalance = address(this).balance;
    }

    // BAD: Indirect state assignment
    function indirectSave() public {
        uint256 bal = address(this).balance;
        savedBalance = bal;
    }

    // BAD: require with strict equality
    function requireExact() public view {
        require(address(this).balance == 100 ether, "Must be exactly 100 ETH");
    }

    // GOOD: Greater than or equal comparison
    function checkMinBalance() public view returns (bool) {
        return address(this).balance >= 1 ether;
    }

    // GOOD: Less than comparison
    function checkMaxBalance() public view returns (bool) {
        return address(this).balance < 100 ether;
    }

    // GOOD: Range check (uses >= and <=, not == or !=)
    function checkBalanceRange() public view returns (bool) {
        return address(this).balance >= 1 ether && address(this).balance <= 10 ether;
    }

    // GOOD: Using balance in arithmetic (not strict equality)
    function addToBalance() public view returns (uint256) {
        return address(this).balance + 1 ether;
    }

    // GOOD: Assigning to local variable only (not state)
    function getBalance() public view returns (uint256) {
        uint256 bal = address(this).balance;
        return bal;
    }
}

contract ExternalBalanceTest {
    address public target;
    uint256 public externalBalance;

    constructor(address _target) {
        target = _target;
    }

    // BAD: Strict equality on external address balance
    function checkTargetBalance() public view returns (bool) {
        return target.balance == 1 ether;
    }

    // BAD: Saving external balance to state
    function saveTargetBalance() public {
        externalBalance = target.balance;
    }

    // GOOD: Greater than check on external balance
    function checkTargetMinBalance() public view returns (bool) {
        return target.balance >= 1 ether;
    }
}
