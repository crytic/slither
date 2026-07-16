// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// In Solidity 0.8+, the compiler prevents msg.value in non-payable public/external functions.
// But it doesn't catch INTERNAL functions that use msg.value when only called from non-payable entry points.
// This detector catches those cases.

contract TestMsgValueInNonPayable {
    mapping(address => uint256) public balances;

    // BAD: Internal function using msg.value, only called from non-payable
    function _addBalance() internal {
        balances[msg.sender] += msg.value;
    }

    function bad1() external {
        _addBalance();
    }

    // BAD: Internal helper in call chain with no payable entry
    function _helper() internal view returns (uint256) {
        return msg.value;
    }

    function _middle() internal view returns (uint256) {
        return _helper();
    }

    function bad2() external view returns (uint256) {
        return _middle();
    }

    // GOOD: Internal function called from payable entry point
    function _processPayment() internal {
        balances[msg.sender] += msg.value;
    }

    function good1() external payable {
        _processPayment();
    }

    // GOOD: Internal function reachable from at least one payable function
    function _sharedHelper() internal view returns (uint256) {
        return msg.value;
    }

    function good2_nonpayable() external view returns (uint256) {
        return _sharedHelper();
    }

    function good2_payable() external payable returns (uint256) {
        return _sharedHelper();
    }
}

contract TestMultipleCallers {
    uint256 public value;

    // Internal function with multiple callers - one payable
    function _setValue() internal {
        value = msg.value;
    }

    // Non-payable caller (alone would be BAD)
    function caller1() external {
        _setValue();
    }

    // Payable caller - makes _setValue GOOD
    function caller2() external payable {
        _setValue();
    }

    // _setValue should NOT be flagged because caller2 is payable
}
