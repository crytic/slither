// SPDX-License-Identifier: MIT
pragma solidity >=0.8.13;

contract Repeated {
    bool active = true;
    modifier twice() { _; _; }
    modifier looped() { for (uint i = 0; i < 2; i++) { _; } }
    modifier exclusive(bool a) { if (a) { _; } else { _; } }
    modifier aborted() { _; revert(); _; }
    modifier flip() { _; active = false; _; }
    function parameter(uint a) public pure twice returns (uint) { return ++a; }
    function namedReturn() public pure twice returns (uint r) { r += 1; }
    function loop(uint a) public pure looped returns (uint) { return ++a; }
    function conditionalReturn() public flip returns (uint r) { if (active) { r = 1; } }
    function oneBranch(uint a) public pure exclusive(a > 0) returns (uint) { return ++a; }
    function noRead(uint a) public pure twice returns (uint) { a = 3; return ++a; }
    function noWrite(uint a) public pure twice returns (uint) { return a; }
    function reset() public pure twice returns (uint r) { r = 1; r += 1; }
    function unreachable(uint a) public pure aborted returns (uint) { return ++a; }
    function memoryAlias(uint[] memory a) public pure twice returns (uint) { a[0]++; return a[0]; }
}
