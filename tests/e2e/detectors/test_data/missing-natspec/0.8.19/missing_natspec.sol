// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.19;

contract MissingNatspec {
    uint256 internal value;

    /// @notice Documented external function, should not be flagged
    /// @param newValue the value to store
    function setValue(uint256 newValue) external {
        value = newValue;
    }

    // Not natspec, just a regular comment
    function withdraw(uint256 amount) external {
        require(amount <= value, "too much");
        value -= amount;
    }

    function total() public view returns (uint256) {
        return value;
    }

    // internal/private functions are not part of the public interface
    function _helper() internal view returns (uint256) {
        return value;
    }

    // constructor and receive should be ignored
    constructor() {
        value = 0;
    }

    receive() external payable {}
}
