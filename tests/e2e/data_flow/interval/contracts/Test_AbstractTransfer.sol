// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Test_AbstractTransfer {
    function constantPower() public pure returns (uint8) {
        return 3 ** 2;
    }

    function constantBitwise() public pure returns (uint8) {
        return 10 & 12;
    }

    function boundedCheckedMul(uint8 left, uint8 right) public pure returns (uint8) {
        require(left >= 2 && left <= 5);
        require(right >= 3 && right <= 7);
        return left * right;
    }

    function boundedDivision(uint8 value) public pure returns (uint8) {
        require(value >= 10 && value <= 20);
        return value / 2;
    }

    function boundedModulo(uint8 value) public pure returns (uint8) {
        require(value >= 10 && value <= 20);
        return value % 6;
    }

    function boundedPower(uint8 value) public pure returns (uint8) {
        require(value >= 2 && value <= 3);
        return value ** 2;
    }

    function boundedShift(uint8 value) public pure returns (uint8) {
        require(value >= 8 && value <= 31);
        return value >> 2;
    }

    function boundedBitwise(uint8 value) public pure returns (uint8) {
        require(value <= 15);
        return value & 3;
    }
}
