import "./a.sol";

pragma solidity 0.8.19;

enum B {
  a,
  b
}

contract T {
    Example e = new Example();
    function b() public returns(uint) {
        B b = B.a;
        return 4;
    }
}