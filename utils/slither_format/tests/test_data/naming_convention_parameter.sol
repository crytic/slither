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

  modifier mod (uint c) {
    require (c > 100);
    _;
  }
  
  /* parameter declarations - bad */
  /* function parameter passed to modifier */
  function bar(uint Count) mod (Count) returns(uint) {
    /* parameter declarations - bad */
    return (Count);
  }
  
}

