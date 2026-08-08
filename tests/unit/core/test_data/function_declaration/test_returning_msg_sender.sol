// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestReturningMsgSender {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    // Should return True
    function directSender() internal view returns (address) {
        return msg.sender;
    }

    function aliasSender() internal view returns (address) {
        address a = msg.sender;
        return a;
    }

    function multiAliasSender() internal view returns (address) {
        address a = msg.sender;
        address b = a;
        address c = b;
        return c;
    }

    function reassignSender() internal view returns (address) {
        address a = msg.sender;
        address b = a;
        a = b;
        return a;
    }

    // Should return False
    function conversionSender() internal view returns (address) {
        address a = msg.sender;
        address b = address(uint160(uint256(uint160(a))));
        return b;
    }

    function _getSender() internal view returns (address) {
        return msg.sender;
    }

    function returnsViaInternal() internal view returns (address) {
        return _getSender();
    }

    function unrelatedReturn() internal view returns (address) {
        address a = owner;
        return a;
    }

    function notMsgSender() internal view returns (address) {
        return address(this);
    }

    function notAddress() internal view returns (uint256) {
        address a = msg.sender;
        return 7;
    }
}
