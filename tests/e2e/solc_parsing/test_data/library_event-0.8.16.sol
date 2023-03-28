pragma solidity 0.8.16;

library Lib {
  event Event();
}

contract Test {
  function foo() external {
    emit Lib.Event(); // This line specifically
  }
}

