pragma solidity ^0.4.24;

contract A {
  /* State variable declaration constant - good */
  uint constant NUMBER = 100;
  /* State variable declaration private - good */
  uint private count = 100;
  /* State variable declaration non-constant non-private - good */
  uint maxnum = 999;
  
  function foo() {
    /* State variable uses - good */
    uint i = NUMBER + count + maxnum;
  }
}

contract B {
  /* State variable declaration constant - bad */
  uint constant number = 100;
  /* State variable declaration private - bad */
  uint private Count = 100;
  /* State variable declaration non-constant non-private - good */
  uint Maxnum = 999;
  function foo() {
    /* State variable uses - bad */
    uint i = number + Count + Maxnum;
    Count += i;
  }
}

