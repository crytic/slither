// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface Observer { function observe() external; }

contract StorageWritesCases {
    uint256 total;
    modifier guard() { _; }
    event Intermediate(uint256 value);
    function emitted(uint256 n) external { for (uint256 i; i < n; ++i) { total += i; emit Intermediate(total); } }
    function accumulate(uint256 n) external {
        for (uint256 i; i < n; ++i) { total += i; }
    }
    function withContinue(uint256 n) external {
        for (uint256 i; i < n; ++i) { if (i == 0) continue; total += i; }
    }
    function withBreak(uint256 n) external {
        for (uint256 i; i < n; ++i) { total += i; if (i == 3) break; }
    }
    function doWhileWrite(uint256 n) external {
        uint256 i;
        do { total += i; ++i; } while (i < n);
    }
    function cached(uint256 n) external {
        uint256 local = total;
        for (uint256 i; i < n; ++i) { local += i; }
        total = local;
    }
    function observed(uint256 n, Observer observer) external {
        for (uint256 i; i < n; ++i) { total += i; observer.observe(); }
    }
    function lowLevelCall(uint256 n, address target) external {
        for (uint256 i; i < n; ++i) { total += i; (bool ok,) = target.call(""); if (!ok) return; }
    }
    function resetAfterLoop(uint256 n) external {
        for (uint256 i; i < n; ++i) { total += i; }
        total = 0;
    }
    function observedAfterLoop(uint256 n) external view returns (uint256) { return total + n; }
    function internalCall(uint256 n) external {
        for (uint256 i; i < n; ++i) { total += i; consume(); }
    }
    function consume() internal view returns (uint256) { return total; }
    function earlyReturn(uint256 n) external {
        for (uint256 i; i < n; ++i) { total += i; if (i == 3) return; }
    }
    function reset(uint256 n) external {
        for (uint256 i; i < n; ++i) { total = i; }
    }
    function observedInCondition(uint256 n) external {
        for (uint256 i; i < n && total < 100; ++i) { total += i; }
    }
    function withModifier(uint256 n) external guard {
        for (uint256 i; i < n; ++i) { total += i; }
    }
    function nested(uint256 n) external {
        for (uint256 i; i < n; ++i) { for (uint256 j; j < n; ++j) { total += j; } }
    }
}
