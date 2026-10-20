// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface Observer { function observe() external; }

contract StorageReadsCases {
    uint256 value = 2;
    uint256[] values;
    uint256 constant FIXED = 2;
    uint256 immutable DEPLOYED = 3;
    modifier guard() { _; }
    function invariantRead(uint256 n) external view returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += value; }
    }
    function whileRead(uint256 n) external view returns (uint256 sum) {
        uint256 i;
        while (i < n) { sum += value; ++i; }
    }
    function doWhileRead(uint256 n) external view returns (uint256 sum) {
        uint256 i;
        do { sum += value; ++i; } while (i < n);
    }
    function conditionRead() external view returns (uint256 sum) {
        for (uint256 i; i < value; ++i) { sum += i; }
    }
    function cachedRead(uint256 n) external view returns (uint256 sum) {
        uint256 cached = value;
        for (uint256 i; i < n; ++i) { sum += cached; }
    }
    function changedValue(uint256 n) external returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += value; value += i; }
    }
    function externalCall(uint256 n, Observer observer) external returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += value; observer.observe(); }
    }
    function lowLevelCall(uint256 n, address target) external returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += value; (bool ok,) = target.call(""); if (!ok) return sum; }
    }
    function internalCall(uint256 n) external returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += value; change(); }
    }
    function change() internal { value += 1; }
    function nested(uint256 n) external view returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { for (uint256 j; j < n; ++j) { sum += value; } }
    }
    function noStorage(uint256 n) external view returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += FIXED + DEPLOYED; }
    }
    function arrayLength(uint256 n) external view returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += values.length; }
    }
    function withModifier(uint256 n) external view guard returns (uint256 sum) {
        for (uint256 i; i < n; ++i) { sum += value; }
    }
    function withAssembly(uint256 n) external view returns (uint256 sum) {
        assembly { sum := 0 }
        for (uint256 i; i < n; ++i) { sum += value; }
    }
}
