pragma solidity ^0.4.24;

contract A {

  /* parameter declaration - bad */
  function foo(uint Count) {
    /* parameter use - bad */
    uint i = Count;
  }

  /* parameter declarations - bad */
  function foobar(uint Count, uint Number) returns (uint) {
    /* parameter declarations - bad */
    return (Count+Number);
  }
  
}

